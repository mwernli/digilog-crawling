from abc import ABCMeta, abstractmethod
from DataSourceSlim import DataSourceSlim, ProcessStatus
from SocialMediaAnalysis import SocialMediaAnalysisContext
import spacy
import logging
import os
import numpy as np
from bs4 import BeautifulSoup
from spaczz.matcher import FuzzyMatcher
import datetime
import pandas as pd
from enum import Enum
from collections import Counter
from pprint import pprint


class IDataAnalysis(metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        self.requiremets_checked = False
        self.html_lengths_array = None
        self.crawlresults = None
        self.nlp = None
        self._NLP_MAX_LENGTH = None
        self.hrefs = None
        self.link_text = None
        self.__name = 'IDataAnalysis'
        self.crawl_id = None
        self.analysis_doc = {}
        try:
            self.logger = kwargs['logger']
        except:
            self.logger = self.get_logger()
        self.ds = DataSourceSlim()
        self.load_keywords()
        self.load_pipeline()

    @abstractmethod
    def do_job(self):
        ''' implement in child class '''

    def close(self):
        self.ds.close()

    def get_logger(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        logfilename = os.path.join(dir_path, '../analyzer.log')
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(logfilename)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        return logger

    def load_pipeline(self):
        self.nlp = spacy.load('de_core_news_sm')
        self._NLP_MAX_LENGTH = 2 * 20 ** 6
        self.nlp.max_length = self._NLP_MAX_LENGTH

    def load_mongo_crawl_results(self, crawl_id: int):
        self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': crawl_id})]
        self.html_lengths_array = np.array([len(item['html']) for item in self.crawlresults])
        if len(self.html_lengths_array) == 0:
            self.logger.info('No results found for crawl {crawl_id}')
            return 1
        # self.max_html_lenght = np.quantile(len(self.html_lengths_array), 0.99)
        return 0

    def load_keywords(self, language: str = 'de'):
        if not 'keywords' in self.ds.mongo.db.list_collection_names():
            self.KEYWORDLIST = ['Umzug', 'Gesuch', 'Steuererklaerung', 'Anmeldung', 'ePayment', 'Heimtieranmeldung',
                                'Antrag', 'Passbestellung', 'online']
            doc = {
                'keywordlist': self.KEYWORDLIST,
                'language': 'de'
            }
            self.ds.mongo.db.keywords.insert_one(doc)
        else:
            res = self.ds.mongo.db.keywords.find_one({'language': language})
            if res is None:
                res = self.ds.mongo.db.keywords.find_one()
            self.KEYWORDLIST = res['keywordlist']

    @staticmethod
    def is_pdf(html_page: str) -> bool:
        return 'pdf' in html_page[:100].lower()

    def check_analysis_requirements(self, **kwargs) -> int:
        if 'loc_gov_id' in list(kwargs.keys()):
            self.loc_gov_id = kwargs['loc_gov_id']
        if 'loc_gov_nam' in list(kwargs.keys()):
            self.loc_gov_nam = kwargs['loc_gov_nam']
        if 'loc_gov_url' in list(kwargs.keys()):
            self.loc_gov_url = kwargs['loc_gov_url']

        try:
            self.analysis_doc['loc_gov_id'] = self.loc_gov_id
        except AttributeError:
            missing_attr = 'loc_gov_id'
            raise AttributeError(
                f'class {self.__name} has no Attribute {missing_attr}. Probably the object is not initialized properly')
        try:
            self.analysis_doc['name'] = self.loc_gov_nam
        except AttributeError:
            missing_attr = 'loc_gov_nam'
            raise AttributeError(
                f'class {self.__name} has no Attribute {missing_attr}. Probably the object is not initialized properly')
        try:
            self.analysis_doc['url'] = self.loc_gov_url
        except AttributeError:
            missing_attr = 'loc_gov_url'
            raise AttributeError(
                f'class {self.__name} has no Attribute {missing_attr}. Probably the object is not initialized properly')
        try:
            self.analysis_doc['links_n'] = len(self.crawlresults)
        except AttributeError:
            missing_attr = 'crawlresults'
            raise AttributeError(
                f'class {self.__name} has no Attribute {missing_attr}. Probably the object is not initialized properly')

        self.analysis_doc['crawl_id'] = self.crawl_id
        self.requiremets_checked = True
        return 0

    def run_keyword_analysis(self) -> int:
        if not self.requiremets_checked:
            print('check requirements before running keywords analysis')
            return 1
        if not hasattr(self, 'KEYWORDLIST'):
            self.load_keywords()
        self.analysis_doc['keywords'] = {}
        for keyword in self.KEYWORDLIST:
            self.analysis_doc['keywords'][keyword.lower()] = {}
            self.analysis_doc['keywords'][keyword.lower()]['count'] = 0
            self.analysis_doc['keywords'][keyword.lower()]['match_ratio'] = []
            self.analysis_doc['keywords'][keyword.lower()]['result_id'] = []

        for page in self.crawlresults:
            if self.is_pdf(page['html']):
                continue

            links = [(tag.get_text(), tag.get('href')) for tag in
                     BeautifulSoup(page['html'], features='html.parser').find_all('a')]

            href = [href for text, href in links]
            link_text = [text for text, href in links]

            if self.hrefs is None:
                self.hrefs = href
            else:
                self.hrefs.extend(href)

            if self.link_text is None:
                self.link_text = link_text
            else:
                self.link_text.extend(link_text)

            page_text = ' '.join(
                [token.text for token in self.nlp('. '.join(link_text))
                 if not token.is_stop
                 and not token.is_punct and not token.pos_ == 'SPACE'
                 and not token.pos_ == 'ADP' and not token.pos_ == 'ADJ'
                 and not token.pos_ == 'DET' and not token.pos == 'X']
            )

            doc = self.nlp(page_text)
            matcher = FuzzyMatcher(self.nlp.vocab)
            for keyword in self.KEYWORDLIST:
                matcher.add('NOUN', [self.nlp(keyword)])
                matches = matcher(doc)

                if len(matches) > 0:
                    self.analysis_doc['keywords'][keyword.lower()]['count'] += len(matches)
                    self.analysis_doc['keywords'][keyword.lower()]['match_ratio'].extend(
                        [(str(doc[start:end]), float(ratio), page['result_id']) for match_id, start, end, ratio in
                         matches])
                    self.analysis_doc['keywords'][keyword.lower()]['result_id'].append(page['result_id'])
                else:
                    pass
                matcher.remove('NOUN')

        for keyword in self.KEYWORDLIST:
            if self.analysis_doc['keywords'][keyword.lower()]['count'] > 0:
                tmp_df = pd.DataFrame(self.analysis_doc['keywords'][keyword.lower()]['match_ratio'])
                self.analysis_doc['keywords'][keyword.lower()]['mean'] = tmp_df.iloc[:, 1].mean().round(5)
                self.analysis_doc['keywords'][keyword.lower()]['median'] = tmp_df.iloc[:, 1].median().round(5)
                self.analysis_doc['keywords'][keyword.lower()]['var'] = tmp_df.iloc[:, 1].var().round(5)
            else:
                self.analysis_doc['keywords'][keyword.lower()]['mean'] = 0
                self.analysis_doc['keywords'][keyword.lower()]['median'] = 0
                self.analysis_doc['keywords'][keyword.lower()]['var'] = 0
        return 0

    def run_analysis(self) -> int:
        status = self.run_transparency_analysis()
        status = self.run_keyword_analysis()
        status = self.run_social_media_analysis()
        status = self.run_login_analysis()
        # status = self.run_keyword_analysis()

        # insert into database
        self.analysis_doc['inserted_at'] = datetime.datetime.now()
        try:
            result = self.ds.mongo.db.simpleanalysis.insert_one(self.analysis_doc)
            self.ds.postgres.insert_crawl_analysis(self.crawl_id, str(result.inserted_id), self.analysis_doc['loc_gov_id'])
            self.logger.info(f'crawl {self.crawl_id} analyzed in document {result.inserted_id}')
        except:
            pprint(self.analysis_doc)
            raise

        return 0

    def run_keyphrase_crawl_links_search(self, keyphrase) -> dict:
        # searches all links of a crawl for a certain keywphrase and returns a dict with the amount of matches and no matches
        if self.crawl_id is None:
            raise 'crawl id not initialized'
        crawl_links = self.ds.postgres.get_crawl_result(self.crawl_id)
        if len(crawl_links) == 0:
            return {True: 0, False: 0}

        dic = dict(Counter([keyphrase in url for url in crawl_links.url.values]))
        try:
            return {True: dic[True], False: dic[False]}
        except:
            return {True: 0, False: dic[False]}

    def run_login_analysis(self) -> int:
        keyphrase = 'login'
        res_dict = self.run_keyphrase_crawl_links_search(keyphrase)
        score = int(res_dict[True] > 0)
        n_links_contain = res_dict[True]
        n_links_contain_not = res_dict[False]
        login_score = {
            'score': score,
            'n_links_contain': n_links_contain,
            'n_links_contain_not': n_links_contain_not,
            'keyphrase': keyphrase
        }
        self.analysis_doc['login_score'] = login_score
        return 0

    def run_social_media_analysis(self) -> int:
        with SocialMediaAnalysisContext(crawl_id=self.crawl_id) as sma:
            sma.hrefs = self.hrefs
            # sma.crawl_id = self.crawl_id
            sma.analyze()
            self.analysis_doc['socialmedia_score'] = {
                'score': sma.social_media_score,
                'facebook_account': sma.social_media_dict['facebook']['account'],
                'twitter_account': sma.social_media_dict['twitter']['account'],
                'instagram_account': sma.social_media_dict['instagram']['account'],
                'youtube_account': sma.social_media_dict['youtube']['account']
            }
        return 0

    def get_crawl_loc_gov_data(self, crawl_id):
        res = self.ds.postgres.get_loc_gov_data(crawl_id)
        if res is None:
            res = self.ds.postgres.get_loc_gov_data_alternative(crawl_id)

        try:
            loc_gov_id, loc_gov_url, loc_gov_nam = res
            loc_gov_id = int(loc_gov_id)
            return (loc_gov_id, loc_gov_url, loc_gov_nam)
        except (ValueError, TypeError) as e:
            loc_gov_id, loc_gov_url, loc_gov_nam = res
        # raise ValueError('Could not initialize object, no matching result in the repository for crawled homepage')

        return (None, loc_gov_url, None)


class AnalysisQueued(IDataAnalysis):
    __name = 'AnalysisQueued'
    __instance = None

    @staticmethod
    def get_instance(*args, **kwargs):
        if AnalysisQueued.__instance == None:
            return None
        return AnalysisQueued.__instance

    def __init__(self, *args, **kwargs):
        super(AnalysisQueued, self).__init__(*args, **kwargs)
        self.loc_gov_nam = None
        self.logger.info(f'Setting up class "{self.__name}" analyzer')

    # res = self.ds.postgres.get_loc_gov_data(self.crawl_id)
    # if res is None:
    # 	res = self.ds.postgres.get_loc_gov_data_alternative()
    # try:
    # 	self.loc_gov_id, self.loc_gov_url, self.loc_gov_nam = res
    # 	loc_gov_id = int(loc_gov_id)
    # except ValueError:
    # 	raise ValueError('Could not initialize object, no matching result in the repository for crawled homepage')
    # except TypeError:
    # 	raise TypeError('Could not initialize object, no matching result in the repository for crawled homepage')

    def check_for_updates(self) -> bool:
        result = self.ds.postgres.get_next_crawl_for_analysis()
        self.crawl_id = result
        if result is None:
            return False
        return True

    def do_job(self):
        self.loc_gov_id, self.loc_gov_url, self.loc_gov_nam = self.get_crawl_loc_gov_data(self.crawl_id)
        status = self.load_mongo_crawl_results(self.crawl_id)
        if status == 1:
            self.ds.postgres.insert_crawl_status(self.crawl_id,
                                                 ProcessStatus.ANALYSIS_WARNING__NO_CRAWLING_RESULTS_FOUND)
            return
        status = self.check_analysis_requirements()
        status = self.run_analysis()
        if status == 0:
            if self.loc_gov_id is None or self.loc_gov_nam is None:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED__NO_MUNICIPALITY_MATCH)
            else:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED)


class AnalysisAll(IDataAnalysis):
    __name = 'AnalysisAll'

    def __init__(self, *args, **kwargs):
        super(AnalysisAll, self).__init__()
        self.logger.info(f'Setting up class "{self.__name}" analyzer')
        self.run_all()

    def run_all(self):
        pass

    def do_job(self):
        self.ds.postgres.update_crawl_status(self.crawl_id, ProcessStatus.ANALYZING)
        self.loc_gov_id, self.loc_gov_url, self.loc_gov_nam = self.get_crawl_loc_gov_data(self.crawl_id)
        status = self.load_mongo_crawl_results(self.crawl_id)
        if status == 1:
            self.ds.postgres.insert_crawl_status(self.crawl_id,
                                                 ProcessStatus.ANALYSIS_WARNING__NO_CRAWLING_RESULTS_FOUND)
            return
        status = self.check_analysis_requirements()
        status = self.run_analysis()
        if status == 0:
            if self.loc_gov_id is None or self.loc_gov_nam is None:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED__NO_MUNICIPALITY_MATCH)
            else:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED)


class AnalysisSingle(IDataAnalysis):
    __name = 'AnalysisSingle'

    def __init__(self, *args, **kwargs):
        super(AnalysisSingle, self).__init__()
        self.logger.info(f'Setting up class "{self.__name}" analyzer')
        self.crawl_id = kwargs['crawl_id']

    # self.do_job()

    def do_job(self):
        self.ds.postgres.update_crawl_status(crawl_id=self.crawl_id, status=ProcessStatus.ANALYZING)
        self.loc_gov_id, self.loc_gov_url, self.loc_gov_nam = self.get_crawl_loc_gov_data(self.crawl_id)
        status = self.load_mongo_crawl_results(self.crawl_id)
        if status == 1:
            self.ds.postgres.insert_crawl_status(self.crawl_id,
                                                 ProcessStatus.ANALYSIS_WARNING__NO_CRAWLING_RESULTS_FOUND)
            return
        status = self.check_analysis_requirements()
        status = self.run_analysis()
        if status == 0:
            if self.loc_gov_id is None or self.loc_gov_nam is None:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED__NO_MUNICIPALITY_MATCH)
            else:
                self.ds.postgres.insert_crawl_status(self.crawl_id, ProcessStatus.ANALYZED)


class AnalysisFactory:
    __instance = None

    @staticmethod
    def build_analyis(analysis_type: str, *args, **kwargs):
        if analysis_type == 'queued':
            instance = AnalysisQueued.get_instance()
            if instance is None:
                return AnalysisQueued(*args, **kwargs)
            else:
                return instance
        if analysis_type == 'queued_v1.0':
            instance = AnalysisQueued.get_instance()
            if instance is None:
                return AnalysisQueued(*args, **kwargs)
        if analysis_type == 'all':
            return AnalysisAll(*args, **kwargs)
        if analysis_type == 'single':
            return AnalysisSingle(*args, **kwargs)
        raise ValueError('Invalid analysis_type value')


class DataAnalysisContext:

    def __init__(self, analysis_type: str, *args, **kwargs):
        self._da = AnalysisFactory.build_analyis(analysis_type, *args, **kwargs)

    def __enter__(self):
        return self._da

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._da.ds.close()
        del self._da
