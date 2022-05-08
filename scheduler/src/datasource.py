import json
import logging
import os
from typing import List, Dict, Optional

import psycopg2

from model import Municipality

logger = logging.getLogger(__name__)


def get_env_str(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        raise ValueError(f'Environment variable "{name}" is not set')


def get_env_str_or(name: str, default: str) -> str:
    try:
        return get_env_str(name)
    except ValueError:
        return default


def get_env_int(name: str) -> int:
    return int(get_env_str(name))


def get_env_int_or(name: str, default: int) -> int:
    return int(get_env_str_or(name, str(default)))


class DataSource:
    def __init__(self):
        self.postgres = PostgresConnection()

    def close(self):
        self.postgres.close()


class PostgresConnection:
    def __init__(self, called_from_container: bool = True):
        if called_from_container:
            self.host = get_env_str_or('POSTGRES_SERVICE_HOST', 'digilog-postgres')
            self.port = get_env_int_or('POSTGRES_SERVICE_PORT', 5432)
            self.user = get_env_str_or('POSTGRES_USER', 'digilog')
            self.password = get_env_str_or('POSTGRES_PASSWORD', 'password')
            self.db = get_env_str_or('POSTGRES_DB', 'digilog')
            self.schema = get_env_str_or('POSTGRES_DB', 'digilog')
        else:
            self.host = 'localhost'
            self.port = 5500
            self.user = 'digilog'
            self.password = 'password'
            self.db = 'digilog'
            self.schema = 'digilog'
        self.connection = self._connect()

    def _connect(self):
        connection = psycopg2.connect(
            dbname=self.db,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )
        return connection

    def close(self):
        self.connection.close()

    def get_default_settings_by_key(self, settings_key: str) -> dict:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT settings FROM default_scrapy_settings
                    WHERE key = %s
                    """,
                    (settings_key,)
                )
                result = cursor.fetchone()
                if not result:
                    raise KeyError(f'Invalid default settings key "{settings_key}"')
                return result[0]

    def municipalities_with_urls(self, limit: Optional[int], uncalibrated_only: bool) -> List[Municipality]:
        with self.connection as connection:
            with connection.cursor() as cursor:
                limit_query = f'LIMIT {limit}' if limit is not None and limit > 0 else ''
                uncalibrated_only = """
                AND NOT EXISTS (
                    SELECT 1 FROM municipality_to_queue_entry mq
                    WHERE mq.municipality_id = m.id
                    AND EXISTS (
                        SELECT 1 FROM crawling_queue q
                        WHERE q.id = mq.queue_id
                        AND q.crawl_type = 'calibration'
                    )
                )
                """ if uncalibrated_only else ''
                cursor.execute(
                    f"""
                    SELECT id, name_de, url FROM municipality m
                    WHERE m.url <> ''
                    {uncalibrated_only}
                    {limit_query}
                    """
                )
                return [Municipality(r[0], r[1], r[2]) for r in cursor.fetchall()]

    def get_municipality_by_id(self, m_id: int) -> Municipality:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name_de, url FROM municipality
                    WHERE id = %s
                    """,
                    (m_id,)
                )
                result = cursor.fetchone()
                if not result:
                    raise KeyError(f'Municipality "{m_id}" not found.')
                return Municipality(result[0], result[1], result[2])

    def schedule_municipality_calibration_runs(self, configuration: Dict[Municipality, dict]):
        with self.connection as connection:
            with connection.cursor() as cursor:
                for municipality, settings in configuration.items():
                    cursor.execute(
                        """
                        INSERT INTO crawling_queue (
                            top_url,
                            status,
                            priority,
                            inserted_at,
                            updated_at,
                            reason,
                            crawl_type,
                            scrapy_settings
                        )
                        VALUES (%s, 'NEW', 1, NOW(), NOW(), '', 'calibration', %s)
                        RETURNING id
                        """,
                        (municipality.url, json.dumps(settings),)
                    )
                    queue_id = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        INSERT INTO municipality_to_queue_entry (municipality_id, queue_id)
                        VALUES (%s, %s)
                        """,
                        (municipality.id, queue_id)
                    )

                    logger.info(f'scheduled calibration run {queue_id} for {municipality.name_de}')
