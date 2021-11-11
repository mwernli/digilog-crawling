from pymongo import MongoClient
import psycopg2
from pprint import pprint


class MongoDbConnection:
    def __init__(self):
        self.mongo()

    def mongo(self):
        host = 'localhost'
        port = 27017
        port1 = 5550
        user = 'root'
        password = 'mongopwd'
        connection_string = 'mongodb://{}:{}@{}:{}'.format(user, password, host, port1)

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
        self.host = 'localhost'
        self.port = '5500'
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