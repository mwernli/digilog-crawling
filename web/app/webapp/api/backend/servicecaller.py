import os
from typing import TypeVar, Callable

import psycopg2
from pymongo import MongoClient

from .core.common.model import DataSource


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

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.connection.close()


class MongoDbConnection:
    def __init__(self, called_from_container: bool = True):
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
        with dc.postgres as postgres_connection, dc.mongodb:
            ds = DataSource(postgres_connection, dc.mongodb.db, dc.mongodb.session)
            return handler(ds)


