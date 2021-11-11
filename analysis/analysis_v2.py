import re
import spacy
from spacy.util import filter_spans
from DataSourceSlim import DataSourceSlim
from spaczz.matcher import FuzzyMatcher
import numpy as np
import logging
import os

nlp = spacy.load('de_core_news_sm')
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

print(start_crawl_id)
print(end_crawl_id)

for crawl_id in range(start_crawl_id, end_crawl_id + 1):    
    result = ds.mongo.db.simpleresults.find({'crawl_id': crawl_id})
    obj = [item for item in result]
    analysis_doc = {}

    doc = ' '.join([nlp(page['raw_text']) for page in obj])
    matcher = FuzzyMatcher(nlp.vocab)
        
    for keyword in KEYWORDLIST:
        analysis_doc[keyword.lower()] = {}
        matcher.add("NOUN", [nlp(keyword)])
        matches = matcher(doc)
        analysis_doc[keyword.lower()]['count'] = len(matches)
        analysis_doc[keyword.lower()]['match_ratio'] = [(doc[start:end], ratio) for match_id, start, end, ratio in matches]
        tmp_ar = np.array(analysis_doc[keyword.lower()]['match_ratio'])
        analysis_doc[keyword.lower()]['mean'] = tmp_ar[:,1].mean()
        analysis_doc[keyword.lower()]['median'] = np.median(tmp_ar[:,1])
        matcher.remove('NOUN')

        
        
        
    # result = ds.mongo.db.simpleanalysis.insert_one(analysis_doc)
    logger.info(f'crawl {crawl_id} analyzed in document {result}')

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