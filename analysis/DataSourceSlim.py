from pymongo import MongoClient
import psycopg2
from pprint import pprint
import os


class MongoDbConnection:
    def __init__(self):
        self.mongo()

    def mongo(self):
        try:
            if os.environ['OUTSIDE_NETWORK'] == '1':
                self.host = 'localhost'
                self.port = 5550
            else:
                self.host = 'digilog-mongodb'
                self.port = 27017
        except :
            self.host = 'digilog-mongodb'
            self.port = 27017
        self.user = 'root'
        self.password = 'mongopwd'
        connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)

        # project_wd = '/home/ubuntu/testfolder/digilog-analysis-ssh'
        # deployment_wd = '/home/ubuntu/digilog/digilog-crawling'

        client = MongoClient(connection_string)
        self.db = client.digilog
        # self.db.list_collection_names()

        # self.simpleresults  = self.db['simpleresults']
        
    def insert_mongo_analysis(self, doc: dict):
        result = self.db.crawlanalysis.insert_one(doc)
        return result.inserted_id


class PostresDbConnection:
    """docstring for PostresDbConnection"""
    def __init__(self):
        self.postgres()

    def postgres(self):
        try:
            if os.environ['OUTSIDE_NETWORK'] == '1':
                self.host = 'localhost'
                self.port = '5500'
            else:
                self.host = 'digilog-postgres'
                # self.host = 'database'
                self.port = 5432
        except psycopg2.OperationalError:
            self.host = 'digilog-postgres'
            # self.host = 'database'
            self.port = 5432

        self.user = 'digilog'
        self.password = 'password'
        self.db = 'digilog'
        self.schema = 'digilog'
        # self.sql_statement = 'select url from loc_gov_ch'
        self.connection = psycopg2.connect(
            dbname=self.db,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def interact_postgres(self, sql_statement = None):
        cursor = self.connection.cursor()
        cursor.execute(sql_statement)
        result = cursor.fetchall()
        return result

class DataSourceSlim:
    def __init__(self):
        self.mongo = MongoDbConnection()
        self.postgres = PostresDbConnection()
