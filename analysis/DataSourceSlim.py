from pymongo import MongoClient
import psycopg2
from pprint import pprint
from dataclasses import dataclass
import os
from enum import Enum


class ProcessStatus(Enum):
    CRAWLING = 1
    CRAWLED = 2
    CRAWL_ERROR = 3
    ANALYZING = 4
    ANALYZED = 5
    ANALYSIS_ERROR = 6
    ANALYSIS_WARNING__NO_CRAWLING_RESULTS_FOUND = 7


@dataclass
class QueuedStatusEntry:
    crawl_id: int
    status: str


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


class MongoDbConnection:
    def __init__(self):
        self.password = None
        self.user = None
        self.port = None
        self.host = None
        self.mongo()

    def mongo(self):
        # try:
        if os.environ['OUTSIDE_NETWORK'] == '0':
            self.host = get_env_str_or('MONGODB_SERVICE_HOST', 'digilog-mongodb')
            self.port = get_env_int_or('MONGODB_SERVICE_PORT', 27017)
            self.user = get_env_str_or('MONGODB_USER', 'mongoDbUser')
            self.password = get_env_str_or('MONGODB_PASSWORD', 'mongoDbPass')
        else:

            # self.host = 'localhost'
            # self.port = 5550
            # self.user = 'root'
            # self.password = 'mongopwd'

            self.host = 'localhost'
            self.port = 27017
            self.user = 'mongoDbUser'
            self.password = 'mongoDbPass'

        self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
        self.client = MongoClient(self.connection_string)
        self.db = self.client.digilog

    def insert_mongo_analysis(self, doc: dict):
        result = self.db.crawlanalysis.insert_one(doc)
        return result.inserted_id

    def close(self):
        self.client.close()


class PostresDbConnection:
    """docstring for PostresDbConnection"""

    def __init__(self):
        self.schema = None
        self.password = None
        self.db = None
        self.user = None
        self.port = None
        self.host = None
        self.postgres()

    def postgres(self):
        if os.environ['OUTSIDE_NETWORK'] == '0':
            self.host = get_env_str_or('POSTGRES_SERVICE_HOST', 'digilog-postgres')
            self.port = get_env_int_or('POSTGRES_SERVICE_PORT', 5432)
            self.user = get_env_str_or('POSTGRES_USER', 'digilog')
            self.password = get_env_str_or('POSTGRES_PASSWORD', 'password')
            self.db = get_env_str_or('POSTGRES_DB', 'digilog')
            self.schema = get_env_str_or('POSTGRES_DB', 'digilog')
        else:
            # #Access to Docker-Network
            # self.host = 'localhost'
            # self.port = 5500
            # self.user = 'digilog'
            # self.password = 'password'
            # self.db = 'digilog'
            # self.schema = 'digilog'

            # Access to Kubernetes Network
            self.host = 'localhost'
            self.port = 5432
            self.user = 'digilog'
            self.password = 'digilogDbPass'
            self.db = 'digilog'
            self.schema = 'digilog'

        self.connection = psycopg2.connect(
            dbname=self.db,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def interact_postgres(self, sql_statement=None):
        cursor = self.connection.cursor()
        cursor.execute(sql_statement)
        result = cursor.fetchall()
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

    def get_next_crawl_for_analysis(self) -> int:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        UPDATE crawl_run_status
                        SET status = '{ProcessStatus.ANALYZING}'
                        WHERE crawl_id = (
                            SELECT crawl_id FROM crawl_run_status
                            WHERE (status = 'CRAWLED') 
                            OR (status = '{ProcessStatus.CRAWLED}')
                            LIMIT 1
                            FOR UPDATE SKIP LOCKED
                        ) RETURNING crawl_id;
                        """
                )
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result[0]

    def update_crawl_status(self, status: str, crawl_id: int):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE crawl_run_status
                    SET status = '{status}'
                    WHERE crawl_id = {crawl_id}
                    """
                )

    def get_loc_gov_data(self, crawl_id: int) -> tuple[int, str, str]:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'''
                    SELECT municipality.id, municipality.url, municipality.name_de
                    FROM municipality 
                    LEFT JOIN crawl ON municipality.url = crawl.top_url 
                    WHERE crawl.id = {crawl_id}'''
                )
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result

    def get_loc_gov_data_alternative(self, crawl_id: int) -> tuple[int, str, str]:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'SELECT (crawl.top_url) FROM crawl WHERE id = {crawl_id}'
                )
                url = cursor.fetchone()[0].split("//")[-1]
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT id, url, name_de FROM municipality where url ~'{url}'"
                )
                res = cursor.fetchone()
        # print(gov_url)
        if not res:

            # ids = [ind for ind, gov_url in gov_urls if bool(re.search(url, gov_url))]
            # if len(ids) == 0:
            return (None, url, None)
        else:
            return res
            # with self.connection as connection:
            #     with connection.cursor() as cursor:
            #         cursor.execute(
            #             'SELECT id, url, name_de FROM loc_gov_ch WHERE id = %s',(gov_url[0],)
            #         )
            #         return cursor.fetchone()

    def insert_crawl_analysis(self, crawl_id: int, mongo_id: str, loc_gov_id: int) -> int:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""INSERT INTO crawl_analysis (crawl_id, mongo_analysis_id, log_gov_id)
                    VALUES ({crawl_id}, '{mongo_id}', {loc_gov_id})
                    RETURNING id;""",
                )
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result[0]

    def close(self):
        self.connection.close()


class DataSourceSlim:
    def __init__(self):
        # if not 'OUTSIDE_NETWORK' in list(os.environ.keys()):
        # os.environ['OUTSIDE_NETWORK'] = '1'
        self.mongo = MongoDbConnection()
        self.postgres = PostresDbConnection()

    def close(self):
        self.mongo.close()
        self.postgres.close()


class DataSourceSlimContext:
    def __enter__(self) -> DataSourceSlim:
        self._ds = DataSourceSlim()
        return self._ds

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self._ds.close()
        del self._ds
