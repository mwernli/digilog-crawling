from enum import Enum


class DataSource:
    def __init__(self, postgres_connection, mongodb_db, mongodb_session):
        self._postgres_connection = postgres_connection
        self.mongodb = mongodb_db
        self.mongodb_session = mongodb_session

    def postgres_cursor(self):
        return self._postgres_connection.cursor()


class FlashType(Enum):
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'danger'
