import re
import spacy
from spacy.util import filter_spans
from DataSourceSlim import DataSourceSlim
from spaczz.matcher import FuzzyMatcher
import pandas as pd
import logging
import os
from progressbar import progressbar
from bs4 import BeautifulSoup
import sys
from sqlalchemy import create_engine
import multiprocessing
from multiprocessing import log_to_stderr, get_logger
import datetime
import numpy as np
import subprocess


def analyze()

def get_crawl_id_range():
	postgres_result = ds.postgres.interact_postgres('SELECT crawl_id FROM crawl_analysis ORDER BY crawl_id DESC LIMIT 1;')
	if len(postgres_result) == 0:
	    start_crawl_id = 1
	else:
	    start_crawl_id = int(postgres_result[0][0])+1
	end_crawl_id = ds.postgres.interact_postgres('SELECT id FROM crawl ORDER BY id DESC LIMIT 1;')[0][0]

	return (start_crawl_id, end_crawl_id)

def do_logging(secs):
    time.sleep(secs)
    logger.info(str(secs))
    # print(str(secs))
    

if __name__ == '__main__':
		
	nlp = spacy.load('de_core_news_sm')
	NLP_MAX_LENGTH = 2*10**6 
	nlp.max_length = NLP_MAX_LENGTH
	ds = DataSourceSlim()

	if not 'keywords' in ds.mongo.db.list_collection_names():
	    KEYWORDLIST = ['Umzug', 'Gesuch', 'Steuererklaerung', 'Anmeldung', 'ePayment', 'Heimtieranmeldung', 'Antrag', 'Passbestellung']
	    doc = {
	        'keywordlist' : KEYWORDLIST
	    }
	    ds.mongo.db.keywords.insert_one(doc)
	else:
	    mongo_keywords = ds.mongo.db.keywords.find({})
	    KEYWORDLIST = [item for item in mongo_keywords][0]['keywordlist']



	# Logger
	dir_path = os.path.dirname(os.path.realpath(__file__))
	filename = os.path.join(dir_path, 'periodical_analysis.log')
	log_to_stderr() #prints in console
	logger = get_logger()
	logger.setLevel(logging.INFO)


	file_handler = logging.FileHandler(filename)
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
	logger.addHandler(file_handler)

	start_crawl_id, end_crawl_id = get_crawl_id_range() #range of which crawls are analyzed
	logger.info(f'analyzing crawls from id{start_crawl_id} to {end_crawl_id}')

    with multiprocessing.Pool(5) as pool:
        for i in pool.imap_unordered(analyze, urls):
            pass
