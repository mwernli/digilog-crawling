from importlib.machinery import SourceFileLoader
from pymongo import MongoClient
module, path = 'DataSource', '/home/ubuntu/digilog/digilog-crawling/scrapy/digilog/digilog/DataSource.py'
DataSource = SourceFileLoader(module,path).load_module()
# class MongoDbConnection:
#     def __init__(self, port: int = 27017):
#         self.host = 'digilog-mongodb'
#         self.port = port
#         self.user = 'root'
#         self.password = 'mongopwd'
#         self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
#         self.client = MongoClient(self.connection_string)
#         self.db = self.client.digilog
#
#     def insert_crawl_result(self, crawl_id: int, result_id: int, html: str, raw_text: str) -> ObjectId:
#         doc = {
#             'crawl_id': crawl_id,
#             'result_id': result_id,
#             'html': html,
#             'raw_text': raw_text
#         }
#         result = self.db.simpleresults.insert_one(doc)
#         return result.inserted_id
#
#     def close(self):
#         self.client.close()

host = 'localhost'
port = 27017
port1 = 5550
user = 'root'
password = 'mongopwd'
connection_string = 'mongodb://{}:{}@{}:{}'.format(user, password, host, port1)

project_wd = '/home/ubuntu/testfolder/digilog-analysis-ssh'
deployment_wd = '/home/ubuntu/digilog/digilog-crawling'

client = MongoClient(connection_string)
db = client.digilog
db.list_collection_names()