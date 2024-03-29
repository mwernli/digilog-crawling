import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Callable, Optional

import psycopg2
from bson import ObjectId
from psycopg2.extras import execute_values
from pymongo import MongoClient
from scrapy.link import Link

_CONDENSE_WS_PATTERN = re.compile(r'\s+')


def condense(s: str) -> str:
    return _CONDENSE_WS_PATTERN.sub(' ', s).strip()


@dataclass(frozen=True)
class QueueEntry:
    id: int
    url: str
    crawl_type: str
    settings: dict


class QueueStatus(Enum):
    NEW = 'NEW'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'
    ERROR = 'ERROR'
    CRAWLED = 'CRAWLED'


class ProcessStatus(Enum):
    CRAWLING = 1
    CRAWLED = 2
    CRAWL_ERROR = 3
    ANALYZING = 4
    ANALYZED = 5
    ANALYSIS_ERROR = 6
    ANALYSIS_WARNING__NO_CRAWLING_RESULTS_FOUND = 7


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
            port=self.port
        )
        return connection

    def insert_crawl(self, top_url: str, crawl_type: str) -> int:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO crawl (top_url, crawl_type)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (top_url, crawl_type)
                )
                result = cursor.fetchone()[0]
                return result


    def insert_crawl_status(self, crawl_id: int, status: str):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO crawl_run_status (crawl_id, status)
                    VALUES ({crawl_id}, '{status}')
                    ON CONFLICT (crawl_id) 
                    DO UPDATE SET status= excluded.status;
                    """
                    # (crawl_id, status)
                )


    def insert_queue_crawl_connection(self, queue_id: int, crawl_id: int):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO queue_crawl (queue_id, crawl_id)
                    VALUES (%s, %s)
                    """,
                    (queue_id, crawl_id)
                )

    def insert_result_record(self, crawl_id: int, url: str) -> int:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO crawl_result (crawl_id, url, link_text)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (crawl_id, url) DO NOTHING;
                    """,
                    (crawl_id, url, '')
                )
                cursor.execute(
                    """
                    SELECT id from crawl_result
                    WHERE crawl_id = %s AND url = %s
                    """,
                    (crawl_id, url)
                )
                result = cursor.fetchone()[0]
                return result

    def insert_child_links(self, crawl_id: int, links: List[Link], mapper: Callable[[str], str]) -> Dict[str, int]:
        with self.connection as connection:
            with connection.cursor() as cursor:
                urls = set()
                to_insert = []
                for l in links:
                    mapped_url = mapper(l.url)
                    if mapped_url not in urls:
                        to_insert.append((crawl_id, mapped_url, condense(l.text)))
                        urls.add(mapped_url)

                result = execute_values(
                    cursor,
                    """
                    INSERT INTO crawl_result (crawl_id, url, link_text)
                    VALUES %s
                    ON CONFLICT (crawl_id, url) DO UPDATE set link_text = EXCLUDED.link_text 
                    RETURNING id, url
                    """,
                    to_insert,
                    fetch=True,
                )
                children = {}
                for r in result:
                    children[r[1]] = r[0]
                return children

    def update_mongo_id(self, result_id: int, mongo_id: str):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE crawl_result
                    SET mongo_id = %s
                    WHERE id = %s;
                    """,
                    (mongo_id, result_id)
                )
    
    def load_next_queue_entry(self) -> Optional[QueueEntry]:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE crawling_queue
                    SET status = 'PENDING'
                    WHERE id = (
                        SELECT id FROM crawling_queue
                        WHERE status = 'NEW'
                        ORDER BY priority
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    ) RETURNING id, top_url, crawl_type, scrapy_settings;
                    """,
                )
                result = cursor.fetchone()
                if not result:
                    return None
                return QueueEntry(result[0], result[1], result[2], result[3])

    def get_queue_entry_by_id(self, id: int) -> QueueEntry:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, top_url, crawl_type, scrapy_settings
                    FROM crawling_queue
                    WHERE id = %s
                    """,
                    (id,)
                )
                result = cursor.fetchone()
                return QueueEntry(result[0], result[1], result[2], result[3])

    def update_queue_status(self, id: int, status: QueueStatus, reason: str = ''):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE crawling_queue
                    SET status = %s, updated_at = now(), reason = %s
                    WHERE id = %s
                    """,
                    (status.value, reason, id)
                )

    def insert_crawl_stats_connection(self, crawl_id: int, stats_id: str):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO crawl_stats (crawl_id, mongo_stats_id)
                    VALUES (%s, %s)
                    """,
                    (crawl_id, stats_id)
                )


    def close(self):
        self.connection.close()


class MongoDbConnection:
    def __init__(self, called_from_container: bool = True):
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
        self.db = self.client.digilog

    def insert_crawl_result(self, crawl_id: int, result_id: int, html: str) -> ObjectId:
        doc = {
            'crawl_id': crawl_id,
            'result_id': result_id,
            'html': html,
        }
        result = self.db.simpleresults.insert_one(doc)
        return result.inserted_id

    def insert_crawl_stats(self, stats: dict, crawl_id: int, queue_id: Optional[int]) -> ObjectId:
        doc = {
            'crawl_id': crawl_id,
            'stats': stats,
        }
        if queue_id is not None:
            doc['queue_id'] = queue_id

        result = self.db.crawlstats.insert_one(doc)
        return result.inserted_id

    def close(self):
        self.client.close()


class DataSourceContext:
    def __enter__(self) -> DataSource:
        self._ds = DataSource()
        return self._ds

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ds.close()
        del self._ds
