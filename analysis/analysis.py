import re
import spacy
from spacy.util import filter_spans
from DataSourceSlim import DataSourceSlim
from spaczz.matcher import FuzzyMatcher
import numpy as np
import logging
import os
from progressbar import progressbar

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
    page_list = [item for item in result]
    analysis_doc = {}
    for keyword in KEYWORDLIST:
        analysis_doc[keyword.lower()] =  {}
        analysis_doc[keyword.lower()]['count'] = 0
        analysis_doc[keyword.lower()]['match_ratio'] = []
    print(f'analyzing crawl: {crawl_id-start_crawl_id +1}/{end_crawl_id-start_crawl_id +1}')
    for page_i in progressbar(range(len(page_list))):
        # text = page['raw_text']
        if len(page_list[page_i]['raw_text'] < 10**6):
            doc = nlp(page_list[page_i]['raw_text'])
        else:
            continue
        ########
        # text = ' '.join([pate['raw_text'] for page in page_list])
        # doc = nlp(text)
        matcher = FuzzyMatcher(nlp.vocab)
        
        for keyword in KEYWORDLIST:
            # analysis_doc[keyword.lower()] = {}
            matcher.add("NOUN", [nlp(keyword)])
            matches = matcher(doc)
            analysis_doc[keyword.lower()]['count'] += len(matches)
            if len(matches) > 0:
                analysis_doc[keyword.lower()]['match_ratio'] += [(doc[start:end], ratio) for match_id, start, end, ratio in matches]
            matcher.remove('NOUN')


    for keyword in KEYWORDLIST:   
        tmp_ar = np.array(analysis_doc[keyword.lower()]['match_ratio'])
        if analysis_doc[keyword.lower()]['count'] > 0:
            analysis_doc[keyword.lower()]['mean'] = tmp_ar[:,1].mean()
            analysis_doc[keyword.lower()]['median'] = np.median(tmp_ar[:,1])
        else:
            analysis_doc[keyword.lower()]['mean'] = 0
            analysis_doc[keyword.lower()]['median'] = 0
        
    # result = ds.mongo.db.simpleanalysis.insert_one(analysis_doc)
    # logger.info(f'crawl {crawl_id} analyzed in document {result}')
    del result
    del page_list


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