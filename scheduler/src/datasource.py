import logging
import logging
import os
from typing import TypeVar, Callable

import psycopg2
from psycopg2.extras import NamedTupleCursor
from pymongo import MongoClient

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
    def __init__(self, postgres_connection, mongodb_db, mongodb_session):
        self._postgres_connection = postgres_connection
        self.mongodb = mongodb_db
        self.mongodb_session = mongodb_session

    def postgres_cursor(self):
        return self._postgres_connection.cursor()


class PostgresConnection:
    def __init__(self):
        self.host = get_env_str_or('POSTGRES_SERVICE_HOST', 'localhost')
        self.port = get_env_int_or('POSTGRES_SERVICE_PORT', 5500)
        self.user = get_env_str_or('POSTGRES_USER', 'digilog')
        self.password = get_env_str_or('POSTGRES_PASSWORD', 'password')
        self.db = get_env_str_or('POSTGRES_DB', 'digilog')
        self.schema = get_env_str_or('POSTGRES_DB', 'digilog')

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


class MongoDbConnection:
    def __init__(self):
        self.host = get_env_str_or('MONGODB_SERVICE_HOST', 'localhost')
        self.port = get_env_int_or('MONGODB_SERVICE_PORT', 5550)
        self.user = get_env_str_or('MONGODB_USER', 'root')
        self.password = get_env_str_or('MONGODB_PASSWORD', 'mongopwd')

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


R = TypeVar('R')


class DataConnection:
    def __init__(self):
        self.postgres = PostgresConnection()
        self.mongodb = MongoDbConnection()

    def close(self):
        self.postgres.close()
        self.mongodb.close()


class DataConnectionProvider:
    def __enter__(self) -> DataConnection:
        self._dc = DataConnection()
        return self._dc

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dc.close()
        del self._dc


def call(handler: Callable[[DataSource], R]) -> R:
    with DataConnectionProvider() as dc:
        with dc.postgres.connection as postgres_connection, dc.mongodb:
            ds = DataSource(postgres_connection, dc.mongodb.db, dc.mongodb.session)
            return handler(ds)
