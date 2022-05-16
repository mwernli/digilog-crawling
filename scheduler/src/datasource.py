import json
import logging
import os
from typing import List, Dict, Optional

import psycopg2
from bson.objectid import ObjectId
from psycopg2.extras import NamedTupleCursor
from pymongo import MongoClient

from model import Municipality, CalibrationRun

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
        self.mongodb = MongoDbConnection()

    def close(self):
        self.postgres.close()
        self.mongodb.close()


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
            port=self.port,
            cursor_factory=NamedTupleCursor,
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
                    SELECT id, name_de, url, population, area_sqm FROM municipality m
                    WHERE m.url <> ''
                    {uncalibrated_only}
                    {limit_query}
                    """
                )
                return [Municipality.from_named_tuple(r) for r in cursor.fetchall()]

    def get_municipality_by_id(self, m_id: int) -> Municipality:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name_de, url, population, area_sqm FROM municipality
                    WHERE id = %s
                    """,
                    (m_id,)
                )
                result = cursor.fetchone()
                if not result:
                    raise KeyError(f'Municipality "{m_id}" not found.')
                return Municipality.from_named_tuple(result)

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

    def get_finished_calibration_runs(self, limit: Optional[int]) -> List[CalibrationRun]:
        limit_query = f'LIMIT {limit}' if limit is not None and limit > 0 else ''
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                    m.id as m_id,
                    m.name_de,
                    m.url,
                    m.population,
                    m.area_sqm,
                    cq.id as q_id,
                    qc.crawl_id,
                    cs.mongo_stats_id
                    FROM municipality m
                    JOIN municipality_to_queue_entry mtqe ON m.id = mtqe.municipality_id
                    
                    JOIN crawling_queue cq
                    ON cq.id = mtqe.queue_id
                    AND cq.crawl_type = 'calibration'
                    AND cq.status = 'DONE'
                    
                    JOIN queue_crawl qc ON cq.id = qc.queue_id
                    
                    JOIN crawl_stats cs ON qc.crawl_id = cs.crawl_id
                    {limit_query}
                    """
                )
                return [
                    CalibrationRun(
                        Municipality(r.m_id, r.name_de, r.url, r.population, r.area_sqm),
                        r.q_id,
                        r.crawl_id,
                        r.mongo_stats_id,
                    ) for r in cursor.fetchall()]


class MongoDbConnection:
    def __init__(self, called_from_container: bool = False):
        if called_from_container:
            self.host = get_env_str_or('MONGODB_SERVICE_HOST', 'digilog-mongodb')
            self.port = get_env_int_or('MONGODB_SERVICE_PORT', 27017)
            self.user = get_env_str_or('MONGODB_USER', 'root')
            self.password = get_env_str_or('MONGODB_PASSWORD', 'mongopwd')
        else:
            self.host = 'localhost'
            self.port = 5550
            self.user = 'root'
            self.password = 'mongopwd'
        self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
        self.client = MongoClient(self.connection_string)
        self.session = self.client.start_session()
        self.db = self.client.digilog

    def __enter__(self):
        return self.session.start_transaction()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.session.end_session()
        self.client.close()

    def get_crawl_stats(self, stats_id: str) -> dict:
        mongo_stats_id = ObjectId(stats_id)
        result = self.db.crawlstats.find_one({"_id": mongo_stats_id})
        return result['stats']
