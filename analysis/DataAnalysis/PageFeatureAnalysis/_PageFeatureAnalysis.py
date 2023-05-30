import re

from DataSourceSlim import DataSourceSlim
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
class PageFeatureAnalysis:
    """
    contains the features which are analyzed domainwide and not on every single subpage
    """
    def __init__(self, *args, **kwargs):
        self.results_per_page = None
        self.results = {}
        if 'greedy_analysis' in list(kwargs.keys()):
            self.greedy_analysis = bool(kwargs['greedy_analysis'])
        else:
            self.greedy_analysis = True
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        self.ds = DataSourceSlim()
        self.check_data()

    def check_data(self):
        if self.crawlresults is None:
            if self.crawl_id is None:
                print('Neither crawlresults nor crawl_id given, exiting')
                exit()
            else:
                self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]
        else:
            if self.crawl_id is None:
                self.crawl_id = self.crawlresults[0]['crawl_id']

    def run_page_feature_analysis(self):
        self.results_per_page = {}
        for item in self.crawlresults:
            soup = BeautifulSoup(item['html'], features='lxml')
            self.results_per_page[int(item['result_id'])] = {}

            res = self.run_form_analysis(item, soup=soup)
            for key in res['val'].keys():
                self.results_per_page[int(res['key'])][key] = res['val'][key]


    def run_form_analysis(self, item, soup=None):
        """
        returns numerical features about ammount of forms grouped by the number of inputs they contain
        returns bool wether page has login or search bar (with high proabbility)
        """
        if soup is None:
            soup = BeautifulSoup(item['html'], features='lxml')
        forms = soup.find_all('form')
        n_inputs_per_form = np.array([len(form.find_all('input')) for form in forms])
        has_search = any([bool(re.search('search', str(form))) for form in forms])
        has_login = any([bool(form.find_all('input', {'type': re.compile(r'email|password')})) for form in forms])
        res = {
            'key': item['result_id'],
            'val': {
                'n_inputs_form_1': (n_inputs_per_form == 1).sum(),
                'n_inputs_form_2_3': ((n_inputs_per_form > 1) & (n_inputs_per_form < 4)).sum(),
                'n_inputs_form_4_': (n_inputs_per_form > 3).sum(),
                'has_search': int(has_search),
                'has_login': int(has_login)
            }
        }
        return res


class PageFeatureAnalysisContext:
    def __init__(self, **kwargs):
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
    def __enter__(self) -> PageFeatureAnalysis:
        self._st = PageFeatureAnalysis(crawlresults=self.crawlresults)
        return self._st
    def __exit__(self, exc_type, exc_val, exc_tb):
        del self._st


if __name__ == '__main__':
    crawl_id=4249
    pfa = PageFeatureAnalysis(crawl_id=crawl_id)
    pfa.run_page_feature_analysis()
    df = pd.DataFrame(pfa.results_per_page).transpose()
    import matplotlib.pyplot as plt
    plt.imshow(df.corr())
    plt.colorbar()
    plt.show()
    print(df.corr())