from typing import Tuple, Any

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import psycopg2
from pprint import pprint
from dataclasses import dataclass
import os
from enum import Enum
import pandas as pd
import re


if 'OUTSIDE_NETWORK' not in os.environ.keys():
    while True:
        answer = input('inside (0) / outside (1)?')
        if answer in ['0', '1']:
            os.environ['OUTSIDE_NETWORK'] = answer
            break
if os.environ['OUTSIDE_NETWORK'] == '1' and 'LOCAL_NETWORK' not in os.environ.keys():
    while True:
        answer = input('docker network (d) / kubernetes (k)?')
        if answer in ['d', 'k']:
            os.environ['LOCAL_NETWORK'] = answer
            break


class ProcessStatus(Enum):
    CRAWLING = 1
    CRAWLED = 2
    CRAWL_ERROR = 3
    ANALYZING = 4
    ANALYZED = 5
    ANALYSIS_ERROR = 6
    ANALYSIS_WARNING__NO_CRAWLING_RESULTS_FOUND = 7
    ANALYZED__NO_MUNICIPALITY_MATCH = 8


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
            self.user = get_env_str_or('MONGODB_USER', 'root')
            self.password = get_env_str_or('MONGODB_PASSWORD', 'mongopwd')
            self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
            self.client = MongoClient(self.connection_string)
            self.db = self.client.digilog
        else:
            # print(os.environ.keys())

            # self.host = 'localhost'
            # self.port = 5550
            # self.user = 'root'
            # self.password = 'mongopwd'
            # self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
            # self.client = MongoClient(self.connection_string)
            # self.db = self.client.digilog
            if os.environ['LOCAL_NETWORK'] == 'k':
                self.host = 'localhost'
                self.port = 27017
                self.user = 'mongoDbUser'
                self.password = 'mongoDbPass'
                self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
                self.client = MongoClient(self.connection_string)
                self.db = self.client.digilog
            elif os.environ['LOCAL_NETWORK'] == 'd':
                self.host = 'localhost'
                self.port = 5550
                self.user = 'root'
                self.password = 'mongopwd'
                self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
                self.client = MongoClient(self.connection_string)
                self.db = self.client.digilog
            else:
                raise 'no valid input'

    def insert_mongo_analysis(self, doc: dict):
        result = self.db.crawlanalysis.insert_one(doc)
        return result.inserted_id

    def close(self):
        self.client.close()

    def get_results_by_crawl(self, crawl_id: int) -> list:
        return [item for item in self.db.simpleresults.find({'crawl_id': crawl_id})]


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
            self.connection = psycopg2.connect(
                dbname=self.db,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
        else:
            if os.environ['LOCAL_NETWORK'] == 'k':
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
            elif os.environ['LOCAL_NETWORK'] == 'd':
                #Access to Docker-Network
                self.host = 'localhost'
                self.port = 5500
                self.user = 'digilog'
                self.password = 'password'
                self.db = 'digilog'
                self.schema = 'digilog'
                self.connection = psycopg2.connect(
                    dbname=self.db,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
            else:
                raise 'No valid input'

    def interact_postgres(self, sql_statement: str=None):
        cursor = self.connection.cursor()
        cursor.execute(sql_statement)
        result = cursor.fetchall()
        return result

    def interact_postgres_df(self, sql_statement: str):
        cursor = self.connection.cursor()
        cursor.execute(sql_statement)
        colnames = [desc[0] for desc in cursor.description]
        result = cursor.fetchall()
        return pd.DataFrame(data=result, columns=colnames)

    def get_crawls_with_name(self, pattern):
        cursor = self.connection.cursor()
        sql_statement = f'''
        SELECT * 
        FROM crawl
        WHERE top_url LIKE '%{pattern}%'
        '''
        cursor.execute(sql_statement)
        colnames = [desc[0] for desc in cursor.description]
        result = cursor.fetchall()
        return pd.DataFrame(data=result, columns=colnames)


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

    def insert_email_address(self, last_crawl: int, municipality_id: int, email: str):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE municipality_email
                    SET last_crawl = %s, email= %s
                    WHERE municipality_id = %s
                    RETURNING municipality_id;
                    """, (last_crawl, email, municipality_id)
                )
                result = cursor.fetchone()
        if not result:
            with self.connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO municipality_email (municipality_id, last_crawl, email)
                        VALUES (%s, %s, %s)
                        """, (municipality_id, last_crawl, email)
                    )
                    # INSERT OR IGNORE INTO municipality_email (municipality_id, last_crawl, email)
                    # VALUES ({municipality_id}, {last_crawl}, {email})
                    # WHERE municipality_id = {municipality_id}
                    # ON CONFLICT (municipality_id)
                    # DO UPDATE SET last_crawl={last_crawl}, email={email}

    def get_emails_by_country_code(self, code: str):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT * 
                    FROM municipality_email AS me
                    JOIN  municipality On me.municipality_id = municipality.id
                    JOIN state ON state.id = municipality.state_id
                    WHERE state.country_code = '{code}'
                    """
                )
                colnames = [desc[0] for desc in cursor.description]
                result = cursor.fetchall()
                return pd.DataFrame(data=result, columns=colnames)

    def get_summary_crawl_status(self):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'''
                    SELECT r.crawl_id, r.pages, s.status, s.top_url
                    FROM (
                        SELECT crawl_id,
                        count(*) AS pages
                        FROM crawl_result
                        GROUP BY crawl_id
                    ) r
                    LEFT JOIN (
                        SELECT crawl_run_status.status AS status, 
                        crawl_run_status.crawl_id AS crawl_id, 
                        crawl.top_url AS top_url
                        FROM crawl_run_status
                        JOIN crawl ON crawl_run_status.crawl_id = crawl.id  
                    ) s ON s.crawl_id = r.crawl_id;
                    '''
                    # SELECT c.id, count(*), s.status, top_url
                    # FROM ((crawl c
                    # INNER JOIN crawl_result r ON c.id = r.crawl_id)
                    # INNER JOIN crawl_run_status s ON c.id = s.crawl_id)
                    # GROUP BY c.id;
                    # '''
                )
                colnames = [desc[0] for desc in cursor.description]
                result = cursor.fetchall()
                return pd.DataFrame(data=result, columns=colnames).set_index('crawl_id').sort_index()

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

    def get_crawl_result(self, crawl_id: int):
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT * FROM crawl_result where crawl_id = {crawl_id};
                    """
                )
                colnames = [desc[0] for desc in cursor.description]
                result = cursor.fetchall()
                return pd.DataFrame(data=result, columns=colnames)


    def get_loc_gov_data(self, crawl_id: int) -> tuple[int, str, str]:
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'''
                    SELECT top_url
                    FROM crawl
                    WHERE id = {crawl_id}
                    '''
                )
                result = cursor.fetchone()[0]
                url_domain = result.replace('https:', '').replace('http:', '').replace('www.','').replace('/','')
        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'''
                    SELECT municipality.id, municipality.url, municipality.name_de
                    FROM municipality 
                    WHERE municipality.url LIKE '%{url_domain}%'
                    '''
                )
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result

    def get_loc_gov_data_alternative(self, crawl_id: int) -> tuple[None, Any, None] | Any:
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

    def insert_crawl_analysis(self, crawl_id: int, mongo_id: str, loc_gov_id) -> int:

        with self.connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO crawl_analysis (crawl_id, mongo_analysis_id, log_gov_id)
                    VALUES (%s, %s ,%s )
                    RETURNING id;""",
                    (crawl_id, mongo_id, loc_gov_id)
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
