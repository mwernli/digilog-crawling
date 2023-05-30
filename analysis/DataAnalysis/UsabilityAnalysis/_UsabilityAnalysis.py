import re

from DataSourceSlim import DataSourceSlim
from bs4 import BeautifulSoup
import icu


class UsabilityAnalysis:
    """aims to evaluate the usability for disabled people and different languages"""
    def __init__(self, **kwargs):
        self.results = {

        }
        self.results_per_page = None
        if 'n_max' in list(kwargs.keys()):
            self.n_max = kwargs['n_max']
        else:
            self.n_max = None
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None
        self.ds = DataSourceSlim()
        if self.crawlresults is None:
            if self.crawl_id is None:
                exit()
            else:
                self.load_crawl_results_with_crawl_id()

    def run_usability_analysis(self):
        # status = self.get_lang()
        status = self.find_search_form()
        status = self.find_faq_link()

    def run_usability_analysis_per_page(self):
        res = self.find_search_form_per_page()


    def find_faq_link(self):
        self.results['FAQ'] = None
        for page in self.crawlresults:
            res = BeautifulSoup(page['html']).find('a', text=re.compile(r'[f,F]aq|FAQ'))
            if res is not None:
                self.results['FAQ'] = True
                return 0
        self.results['FAQ'] = False
        return 0

    def load_crawl_results_with_crawl_id(self):
        self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]

    def find_search_form_per_page(self, item, soup=None):
        if soup is None:
            soup = BeautifulSoup(item['html'], features='lxml')

    def find_search_form(self) -> int:
        self.results['search_form'] = None
        counter = 0
        if self.n_max is None or self.n_max > 10:
            self.n_max = 10

        for page in self.crawlresults:
            counter += 1
            soup = BeautifulSoup(page['html'])
            status = self.extract_search_form(soup=soup)
            if status == 0:
                self.results['search_form'] = True
                return status
        self.results['search_form'] = False
        return 1

    def extract_search_form(self, soup) -> int:
        tags = soup.find_all('form', {'class': re.compile(r'search')})
        if len(tags) > 0:
            return 0
        else:
            return 1

    def get_multilingual_analysis(self):
        """different languages used"""
        if self.crawlresults is None:
            if self.crawl_id is None:
                exit()
            else:
                self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]



class UsabilityAnalysisContext:
    def __init__(self, **kwargs):
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None

    def __enter__(self) -> UsabilityAnalysis:
        self._ua = UsabilityAnalysis(crawlresults=self.crawlresults, crawl_id=self.crawl_id)
        return self._ua
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass