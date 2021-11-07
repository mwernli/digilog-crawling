from typing import List, Dict, Callable

import psycopg2
from bson import ObjectId
from pymongo import MongoClient
from psycopg2.extras import execute_values
from scrapy.link import Link
import re

_CONDENSE_WS_PATTERN = re.compile(r'\s+')


def condense(s: str) -> str:
    return _CONDENSE_WS_PATTERN.sub(' ', s).strip()


class DataSourceContext:
    def __enter__(self):
        self._ds = DataSource()
        return self._ds

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ds.close()
        del self._ds


class DataSource:
    def __init__(self):
        self.postgres = PostgresConnection()
        self.mongodb = MongoDbConnection()

    def close(self):
        self.postgres.close()
        self.mongodb.close()


class PostgresConnection:
    def __init__(self, called_from_container:bool = True):
        if called_from_container:
            self.host = 'digilog-postgres'
            self.port = 5432
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

    def insert_crawl(self, top_url: str) -> int:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO crawl (top_url)
                    VALUES (%s)
                    RETURNING id
                    """,
                    (top_url,)
                )
                result = cursor.fetchone()[0]
                return result

    def insert_first_result_record(self, crawl_id: int, url: str) -> int:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO crawl_result (crawl_id, url, link_text, parent)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (crawl_id, url, '', None)
                )
                result = cursor.fetchone()[0]
                return result

    def insert_child_links(self, crawl_id: int, parent: int, links: List[Link], mapper: Callable[[str], str]) -> Dict[str, int]:
        with self.connection as connection:
            with connection.cursor() as cursor:
                result = execute_values(
                    cursor,
                    """
                    INSERT INTO crawl_result (crawl_id, url, link_text, parent)
                    VALUES %s
                    ON CONFLICT (crawl_id, url) DO NOTHING
                    RETURNING id, url
                    """,
                    map(lambda l: (crawl_id, mapper(l.url), condense(l.text), parent), links),
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

    def close(self):
        self.connection.close()


class MongoDbConnection:
    def __init__(self, called_from_container:bool = True):
        if called_from_container:
            self.host = 'digilog-mongodb'
            self.port = 27017
        else:
            self.host = 'localhost'
            self.port = 5550
        self.user = 'root'
        self.password = 'mongopwd'
        self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
        self.client = MongoClient(self.connection_string)
        self.db = self.client.digilog

    def insert_crawl_result(self, crawl_id: int, result_id: int, html: str, raw_text: str) -> ObjectId:
        doc = {
            'crawl_id': crawl_id,
            'result_id': result_id,
            'html': html,
            'raw_text': raw_text
        }
        result = self.db.simpleresults.insert_one(doc)
        return result.inserted_id

    def close(self):
        self.client.close()
