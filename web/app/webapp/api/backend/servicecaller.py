import os
from typing import TypeVar, Callable

import psycopg2
from psycopg2.extras import NamedTupleCursor
from pymongo import MongoClient

from .core.common.model import DataSource
from .framework import get_env_str_or, get_env_int_or


class DataConnection:
    def __init__(self):
        try:
            container_network = not bool(int(os.environ['OUTSIDE_NETWORK']))
        except KeyError:
            container_network = True
        self.postgres = PostgresConnection(container_network)
        self.mongodb = MongoDbConnection(container_network)

    def close(self):
        self.postgres.close()
        self.mongodb.close()


class PostgresConnection:
    def __init__(self, called_from_container: bool = True):
        if called_from_container:
            self.host = get_env_str_or('POSTGRES_SERVICE_HOST', 'localhost')
            self.port = get_env_int_or('POSTGRES_SERVICE_PORT', 5500)
            self.user = get_env_str_or('POSTGRES_USER', 'digilog')
            self.password = get_env_str_or('POSTGRES_PASSWORD', 'password')
            self.db = get_env_str_or('POSTGRES_DB', 'digilog')
            self.schema = self.db
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

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.connection.close()


class MongoDbConnection:
    def __init__(self, called_from_container: bool = True):
        if called_from_container:
            self.host = get_env_str_or('MONGODB_SERVICE_HOST', 'localhost')
            self.port = get_env_int_or('MONGODB_SERVICE_PORT', 27017)
            self.user = get_env_str_or('MONGODB_USER', 'digilog')
            self.password = get_env_str_or('MONGODB_PASSWORD', 'digilogDbPass')
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


class DataConnectionProvider:
    def __enter__(self) -> DataConnection:
        self._dc = DataConnection()
        return self._dc

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dc.close()
        del self._dc


R = TypeVar('R')


def call(handler: Callable[[DataSource], R]) -> R:
    with DataConnectionProvider() as dc:
        with dc.postgres.connection as postgres_connection, dc.mongodb:
            ds = DataSource(postgres_connection, dc.mongodb.db, dc.mongodb.session)
            return handler(ds)


