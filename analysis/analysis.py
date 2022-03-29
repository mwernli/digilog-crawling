import re
import spacy
from spacy.util import filter_spans
from DataSourceSlim import DataSourceSlim
from spaczz.matcher import FuzzyMatcher
import numpy as np
import pandas as pd
import logging
import os
from progressbar import progressbar
from bs4 import BeautifulSoup
import numpy as np


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
logfilename = os.path.join(dir_path, 'crawl_analysis.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(logfilename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


# if 'simpleanalysis' in ds.mongo.db.list_collection_names():
#     cursor = ds.mongo.db.simpleanalysis.find().sort([('_id', -1)]).limit(1)
#     start_crawl_id = [item for item in cursor][0]['crawl_id']
# else:
#     start_crawl_id = 1
postgres_result = ds.postgres.interact_postgres('SELECT crawl_id FROM crawl_analysis ORDER BY crawl_id DESC LIMIT 1;')
if len(postgres_result) == 0:
    start_crawl_id = 1
else:
    start_crawl_id = int(postgres_result[0][0])+1


end_crawl_id = ds.postgres.interact_postgres('SELECT id FROM crawl ORDER BY id DESC LIMIT 1;')[0][0]

# start_crawl_id, end_crawl_id = 60,70

logger.info(f'analyzing crawls from id{start_crawl_id} to {end_crawl_id}')
print(f'analyzing crawls from crawl_id {start_crawl_id} to {end_crawl_id}')

for crawl_id in progressbar(range(start_crawl_id, end_crawl_id + 1)):    
    if nlp.max_length != NLP_MAX_LENGTH:
        nlp.max_length =  NLP_MAX_LENGTH
        logger.info(f'resetting nlp max_length from {nlp.max_length}to {NLP_MAX_LENGTH}')
    postgres_result = ds.postgres.interact_postgres(f'SELECT (loc_gov_ch.id, loc_gov_ch.url, loc_gov_ch.gdename) FROM loc_gov_ch LEFT JOIN crawl ON loc_gov_ch.url = crawl.top_url WHERE crawl.id = {crawl_id}')
    
    if len(postgres_result) == 0:
        url = ds.postgres.interact_postgres(f'SELECT (crawl.top_url) FROM crawl WHERE id = {crawl_id}')[0][0]
        cursor = ds.postgres.connection.cursor()
        cursor.execute('SELECT (id, url, gdename) FROM loc_gov_ch WHERE url = %s;',(url.split("//")[-1],))
        postgres_result = cursor.fetchall()

    try:
        postgres_result = re.split(',',postgres_result[0][0].replace('(','').replace(')',''))
    except:
        print(f'ERROR in analysis crawl id {crawl_id}, continue')
        continue
    result = ds.mongo.db.simpleresults.find({'crawl_id': crawl_id})
    obj = [item for item in result]
    len_array = np.array([len(item['html']) for item in obj])
    
    if len(len_array) == 0:
        continue

    max_length = np.quantile(len_array, 0.99)

    analysis_doc = {}
    analysis_doc['loc_gov_id'] = int(postgres_result[0])
    analysis_doc['name'] = postgres_result[1]
    analysis_doc['url'] = postgres_result[2]
    analysis_doc['links_n'] = len(obj)
    analysis_doc['crawl_id'] = crawl_id
    analysis_doc['keywords'] = {}
    for keyword in KEYWORDLIST:
            analysis_doc['keywords'][keyword.lower()] =  {}
            analysis_doc['keywords'][keyword.lower()]['count'] = 0
            analysis_doc['keywords'][keyword.lower()]['match_ratio'] = []
            analysis_doc['keywords'][keyword.lower()]['result_id'] = []

    for page in obj:
        # if len(page['html']) > max_length:
        if 'pdf' in page['html'][:100].lower():
            continue
        page_result_id = page['html']
        links = '. '.join([tag.get_text().strip() for tag in BeautifulSoup(page['html'], features='html.parser').find_all('a')])
        page_text = ' '.join(
            [token.text for token in nlp(links) 
            if not token.is_stop 
            and not token.is_punct and not token.pos_ == 'SPACE' 
            and not token.pos_ == 'ADP' and not token.pos_ == 'ADJ' 
            and not token.pos_== 'DET' and not token.pos == 'X']
        )
        doc = nlp(page_text)
        # if len(page['']) > NLP_MAX_LENGTH:
        #     continue
        # else:
        #     page_text = ' '.join([token.text for token in nlp(page['raw_text']) if not token.is_stop and not token.is_punct and not token.pos_ == 'SPACE' and not token.pos_ == 'ADP' and not token.pos_ == 'ADJ' and not token.pos_== 'DET' and not token.pos == 'X'])

        # if len(page_text) > NLP_MAX_LENGTH:
        #     continue
        # else:
        #     doc = nlp(page_text)

        matcher = FuzzyMatcher(nlp.vocab)

        for keyword in KEYWORDLIST:
            matcher.add("NOUN", [nlp(keyword)])
            matches = matcher(doc)
            
            if len(matches) > 0:
                analysis_doc['keywords'][keyword.lower()]['count'] += len(matches)
                # saves word, match_ratio and result_id of document it appears on
                analysis_doc['keywords'][keyword.lower()]['match_ratio'].extend([(str(doc[start:end]), float(ratio), page['result_id']) for match_id, start, end, ratio in matches])
                analysis_doc['keywords'][keyword.lower()]['result_id'].append(page['result_id'])
            else:
                pass
            matcher.remove('NOUN')
        del page_result_id

    for keyword in KEYWORDLIST:
        if analysis_doc['keywords'][keyword.lower()]['count'] > 0:
            tmp_df = pd.DataFrame(analysis_doc['keywords'][keyword.lower()]['match_ratio'])
            analysis_doc['keywords'][keyword.lower()]['mean'] = tmp_df.iloc[:,1].mean().round(5)
            analysis_doc['keywords'][keyword.lower()]['median'] = tmp_df.iloc[:,1].median().round(5)
            analysis_doc['keywords'][keyword.lower()]['var'] = tmp_df.iloc[:,1].var().round(5)
        else:
            analysis_doc['keywords'][keyword.lower()]['mean'] = 0
            analysis_doc['keywords'][keyword.lower()]['median'] = 0
            analysis_doc['keywords'][keyword.lower()]['var'] = 0
    
        
        
        
    result = ds.mongo.db.simpleanalysis.insert_one(analysis_doc)
    cursor = ds.postgres.connection.cursor()
    cursor.execute('INSERT INTO crawl_analysis (crawl_id, mongo_analysis_id, loc_gov_id) VALUES (%s, %s, %s) RETURNING id;' % (crawl_id, str(result.inserted_id), analysis_doc["loc_gov_id"]))
    analysis_id = cursor.fetchone()[0]
    ds.postgres.connection.commit()
    cursor.close()
    logger.info(f'crawl {crawl_id} analyzed in document {result.inserted_id}')
