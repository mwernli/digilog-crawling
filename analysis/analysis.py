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

nlp = spacy.load('de_core_news_sm')
NLP_MAX_LENGTH = 2*10**6 
nlp.max_length = NLP_MAX_LENGTH

ds = DataSourceSlim()
KEYWORDLIST = ['Umzug', 'Gesuch', 'Steuererklaerung', 'Anmeldung', 'ePayment', 'Heimtieranmeldung', 'Antrag', 'Passbestellung']


# Logger
dir_path = os.path.dirname(os.path.realpath(__file__))
logfilename = os.path.join(dir_path, 'crawl_analysis.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(logfilename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

if 'simpleanalysis' in ds.mongo.db.list_collection_names():
    cursor = ds.mongo.db.simpleanalysis.find().sort([('_id', -1)]).limit(1)
    start_crawl_id = [item for item in cursor][0]['crawl_id']
else:
    start_crawl_id = 1

end_crawl_id = ds.postgres.interact_postgres('SELECT id FROM crawl ORDER BY id DESC LIMIT 1;')[0][0]

# print(start_crawl_id)
# print(end_crawl_id)

for crawl_id in progressbar(range(start_crawl_id, end_crawl_id + 1)):    
# for crawl_id in [1]: 
    if nlp.max_length != NLP_MAX_LENGTH:
        nlp.max_length =  NLP_MAX_LENGTH
        logger.info(f'resetting nlp max_length from {nlp.max_length}to {NLP_MAX_LENGTH}')

    result = ds.mongo.db.simpleresults.find({'crawl_id': crawl_id})
    obj = [item for item in result]
    pages_n = len(obj)
    analysis_doc = {}
    analysis_doc['links_n'] = pages_n
    analysis_doc['crawl_id'] = crawl_id
    full_text = ' '.join([token.text
                    for page in obj
                    if len(page['raw_text']) < 5*10**4
                    for token in nlp(page['raw_text'])
                    if not token.is_stop and not token.is_punct and not token.pos_ == 'SPACE' and not token.pos_ == 'ADP' and not token.pos_ == 'ADJ' and not token.pos_== 'DET' and not token.pos == 'X'])
    if len(full_text) > nlp.max_length:
        logger.info(f'length {len(full_text)} of document exceeds nlp.max_length ({nlp.max_length}) -> setting new max_length')
        print(f'length {len(full_text)} of document exceeds nlp.max_length ({nlp.max_length}) -> setting new max_length')
        nlp.max_length = len(full_text) + 10**4
        doc = nlp(full_text)
    else:
        doc = nlp(full_text)
    matcher = FuzzyMatcher(nlp.vocab)
        
    for keyword in KEYWORDLIST:
        analysis_doc[keyword.lower()] = {}
        matcher.add("NOUN", [nlp(keyword)])
        matches = matcher(doc)
        # counter = 0
        # for match_id, start, end, ratio in matches:
        #     counter += 1
        #     print(match_id, doc[start:end], ratio)
        #     if counter > 10:
        #         print('...')
        #         break
        analysis_doc[keyword.lower()]['count'] = len(matches)
        if analysis_doc[keyword.lower()]['count'] > 0:
            analysis_doc[keyword.lower()]['match_ratio'] = [(str(doc[start:end]), float(ratio)) for match_id, start, end, ratio in matches]
            tmp_df = pd.DataFrame(analysis_doc[keyword.lower()]['match_ratio'])
            analysis_doc[keyword.lower()]['mean'] = tmp_df.iloc[:,1].mean()
            analysis_doc[keyword.lower()]['median'] = tmp_df.iloc[:,1].median()
        else:
            # analysis_doc[keyword.lower()]['count'] = None
            analysis_doc[keyword.lower()]['match_ratio'] = None
            analysis_doc[keyword.lower()]['mean'] = 0
            analysis_doc[keyword.lower()]['median'] = 0
        # analysis_doc[keyword.lower()]['mean'] = tmp_ar[:,1].mean()
        # analysis_doc[keyword.lower()]['median'] = np.median(tmp_ar[:,1])
        matcher.remove('NOUN')
    # from pprint import pprint
    
        
        
        
    result = ds.mongo.db.simpleanalysis.insert_one(analysis_doc)
    logger.info(f'crawl {crawl_id} analyzed in document {result.inserted_id}')

# ###############

# # nlp = spacy.blank("de")
# text = """Grint Anderson created spaczz in his home at 555 Fake St,
# Apt 5 in Nashv1le, TN 55555-1234 in the US."""  # Spelling errors intentional.
# doc = nlp(text)












# matcher.add("NOUN", [nlp("Steuererklärung")])
# matches = matcher(doc)
# print(f'Steuererklärung: {len(matches)}')





#

# import spacy
# from spaczz.pipeline import SpaczzRuler
# nlp = spacy.blank("en")
# ruler = SpaczzRuler(nlp)
# doc = nlp.make_doc("My name is Anderson, Grunt")
# ruler.add_patterns([{"label": "NAME", "pattern": "Grant Andersen",
#                          "type": "fuzzy", "kwargs": {"fuzzy_func": "token_sort"}}])
# doc = ruler(doc)
# "Anderson, Grunt" in [ent.text for ent in doc.ents]