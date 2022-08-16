# from DataSourceSlim import DataSourceSlim
# import numpy as np
# import matplotlib.pyplot as plt

# ds = DataSourceSlim() 
# docs = ds.mongo.db.simpleresults.find({'crawl_id': 524})  
# items = [item for item in docs]     
# ar = np.array([len(item['html']) for item in items])
# desc_ind = ar.argsort()[::-1]
# print(np.quantile(ar, 0.99))
# print(ar[desc_ind][0])

# plt.hist(ar, bins = 100)
# plt.show()

# big_items = [item for item in items if len(item['html']) > 800000]
# big_ar = np.array([item for item in ar if item > 800000])
# big_desc_ind = big_ar.argsort()[::-1]

# plt.plot(
# 	# np.arange(len(ar)-1), 
# 	np.arange(100),
# 	np.diff(ar[desc_ind])[:100]
# )
# plt.show()

from pymongo import MongoClient
import psycopg2
from pprint import pprint
from dataclasses import dataclass
import os
from DataSourceSlim import *

class MongoDbConnectionKubernetes(MongoDbConnection):
    def __init__(self):
        super().__init__()

    def mongo(self):
        self.host = 'localhost'
        self.port = 27017
        self.user = 'mongoDbUser'
        # self.user = 'bW9uZ29EYlVzZXI='
        self.password = 'mongoDbPass'
        # self.password = 'bW9uZ29EYlBhc3M='
        self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
        self.client = MongoClient(self.connection_string)
        self.db = self.client.digilog

class MongoDbConnectionDockerNetwork(MongoDbConnection):
    def __init__(self):
        super().__init__()

    def mongo(self):
        self.host = 'localhost'
        self.port = 27017
        self.user = 'mongoDbUser'
        # self.user = 'bW9uZ29EYlVzZXI='
        self.password = 'mongoDbPass'
        # self.password = 'bW9uZ29EYlBhc3M='
        self.connection_string = 'mongodb://{}:{}@{}:{}'.format(self.user, self.password, self.host, self.port)
        self.client = MongoClient(self.connection_string)
        self.db = self.client.digilog


class PosrgresDbConnectionKubernetes(PostresDbConnection):
    def __init__(self):
        super().__init__()

    def postgres(self):
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

class PosrgresDbConnectionDockerNetwork(PostresDbConnection):
    def __init__(self):
        super().__init__()

    def postgres(self):
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


if __name__ == '__main__':
    mng = MongoDbConnectionKubernetes()
    mng.mongo()
    print(mng.db.list_collection_names())