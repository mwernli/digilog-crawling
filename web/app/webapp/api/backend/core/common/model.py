class DataSource:
    def __init__(self, postgres_connection, mongodb_session):
        self._postgres_connection = postgres_connection
        self._mongodb_session = mongodb_session

    def postgres_cursor(self):
        return self._postgres_connection.cursor()
