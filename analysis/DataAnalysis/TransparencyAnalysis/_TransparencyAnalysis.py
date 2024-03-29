import datetime
import re

import pandas as pd

from DataSourceSlim import DataSourceSlim
from bs4 import BeautifulSoup

class TransparencyAnalysis:
    """aims to evaluate the transparency of a website"""
    def __init__(self, **kwargs):
        self.results_per_page = None
        self.results = {
            'issue_information': []
        }
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

    def run_transparency_analysis(self):
        try:
            self.results['last_modified'] = self.get_last_modification_analysis()
            return 0
        except:
            return 1

    def run_transparency_analysis_per_page(self):
        self.results_per_page = {}
        for item in self.crawlresults:
            soup = BeautifulSoup(item['html'], features='lxml')
            self.results_per_page[item['result_id']] = {}

            res = self.get_last_modification_analysis_per_page(item, soup)
            for key in res['val'].keys():
                self.results_per_page[res['key']][key] = res['val'][key]

            res = self.get_issued_information_per_page(item, soup)
            for key in res['val'].keys():
                self.results_per_page[res['key']][key] = res['val'][key]

    def get_issued_information_per_page(self, item, soup=None):
        if soup is None:
            soup=BeautifulSoup(item['html'], features='lxml')
        # all_pdfs = soup.find_all('a', href=re.compile(r'\.pdf'))
        # all_pdfs.extend(soup.find_all('a', text=re.compile(r'\.pdf')))
        # all_downloads = soup.find_all('a', {'href': re.compile(r'\.pdf'), 'text': re.compile(r'\.pdf|[d,D]ownload')})
        if soup.find_all('a') is None:
            res = {
                'key': item['result_id'],
                'val': {
                    'all_download_texts': None,
                    'n_downloads': 0
                }

            }
        all_downloads = [t.get_text() for t in soup.find_all('a')
                         if 'pdf' in str(t.get('href')) or
                         'pdf' in str(t.get_text() )or
                         bool(re.search(re.compile(r'[d,D]ownload'), str(t.get_text())))]
        # all_downloads = soup.find_all(
        #     lambda t: (t.name=='a' and 'pdf' in t['href']) or
        #               (t.name=='a' and 'pdf' in t.get('text')) or
        #               (t.name=='a' and re.compile(r'[d,D]ownload') in t.get('text'))
        # )
        res = {
            'key': item['result_id'],
            'val': {
                'all_download_texts': ' '.join([tag.replace(' ', '_') for tag in all_downloads]),
                'n_downloads': len(all_downloads)
            }

        }
        return res



    def get_issued_information(self):
        for page in self.crawlresults:
            soup = BeautifulSoup(page['html'])
            all_pdfs = soup.find_all('a', href=re.compile(r'\.pdf'))
            all_pdfs.extend(soup.find_all('a', text=re.compile(r'\.pdf')))
            if len(all_pdfs) == 0:
                all_pdfs = soup.find_all('a', text=re.compile(r'[d,D]ownload'))
            if len(all_pdfs) > 0:
                self.results['issue_information'].extend([tag.text for tag in all_pdfs])

    def get_last_modification_analysis_per_page(self, item, soup=None):
        if soup is None:
            soup = BeautifulSoup(item['html'], features='lxml')

        last_modified = soup.find(name=re.compile(r'[l,L]ast-[m,M]odified'))
        if last_modified is None:
            last_modified = soup.find(property=re.compile(r'[m,M]odified'))
        if last_modified is None:
            res = {
                'key': item['result_id'],
                'val': {
                    'last_mod': None
                }
            }
            return res
        else:
            last_modified = last_modified.get('content')
        last_modified.find(r'\d{4}-\d{2}-\d{2}')
        m = re.search(r'\d{4}-\d{2}-\d{2}', last_modified)
        modified_date = m.string[m.start():m.end()]
        if m is None:
            m = re.search(r'\d{2}-\d{2}-\d{4}', last_modified)
            modified_date = m.string[m.start():m.end()]
            d = datetime.datetime.strptime(modified_date, '%d-%m-%Y')
        else:
            d = datetime.datetime.strptime(modified_date, '%Y-%m-%d')

        sql_statement = f'''
                SELECT inserted_at 
                FROM crawl_result
                WHERE id = {item['result_id']}
                '''

        inserted_at = self.ds.postgres.interact_postgres(sql_statement)[0][0]
        last_modified_day = (inserted_at - d).days
        res = {
            'key': item['result_id'],
            'val': {
                'last_mod': last_modified_day
            }
        }
        return res

    def get_last_modification_analysis(self):

        modified_list = []
        for page in self.crawlresults:
            soup = BeautifulSoup(page['html'], features='lxml')
            last_modified = soup.find(name=re.compile(r'[l,L]ast-[m,M]odified'))
            if last_modified is None:
                last_modified = soup.find(property=re.compile(r'[m,M]odified'))
            if last_modified is None:
                continue
            else:
                last_modified = last_modified.get('content')
            last_modified.find(r'\d{4}-\d{2}-\d{2}')
            m = re.search(r'\d{4}-\d{2}-\d{2}', last_modified)
            modified_date = m.string[m.start():m.end()]
            if m is None:
                m = re.search(r'\d{2}-\d{2}-\d{4}', last_modified)
                modified_date = m.string[m.start():m.end()]
                d = datetime.datetime.strptime(modified_date, '%d-%m-%Y')
            else:
                d = datetime.datetime.strptime(modified_date, '%Y-%m-%d')
            modified_list.append((page['result_id'], page['crawl_id'], d))

        if len(modified_list) == 0:
            return {
            'most_recent_modified': None,
            'oldest_modified': None,
            'median_modified': None,
            'mean_modified': None
        }


        sql_statement = f'''
        SELECT id, inserted_at 
        FROM crawl_result
        WHERE id IN ({", ".join([str(result_id) for result_id, crawl_id, d in modified_list])[1:]})
        '''

        tmp_df = pd.DataFrame(modified_list, columns=['result_id', 'crawl_id', 'last_modified']).set_index('result_id')
        tmp_df = pd.concat([tmp_df, self.ds.postgres.interact_postgres_df(sql_statement).set_index('id')], axis=1)
        tmp_df['time_delta'] = tmp_df.inserted_at - tmp_df.last_modified
        max_val = tmp_df.time_delta.max().round(freq='d')
        min_val  = tmp_df.time_delta.min().round(freq='d')
        median_val = tmp_df.time_delta.median().round(freq='d')
        mean_val = tmp_df.time_delta.mean().round(freq='d')
        return {
            'most_recent_modified': min_val,
            'oldest_modified': max_val,
            'median_modified': median_val,
            'mean_modified': mean_val
        }


class TransparencyAnalysisContext:
    def __init__(self, **kwargs):
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
    def __enter__(self) -> TransparencyAnalysis:
        self._ta = TransparencyAnalysis(crawlresults=self.crawlresults)
        return self._ta
    def __exit__(self, exc_type, exc_val, exc_tb):
        del self._ta

if __name__ == '__main__':
    ta = TransparencyAnalysis(crawl_id=4244)
    ta.run_transparency_analysis_per_page()
    df = pd.DataFrame(ta.results_per_page).transpose()
