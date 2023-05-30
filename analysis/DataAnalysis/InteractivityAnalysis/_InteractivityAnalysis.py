import re
import numpy as np
import pandas as pd
from sklearn import preprocessing
from DataSourceSlim import DataSourceSlim
from collections import Counter
from bs4 import BeautifulSoup
# from SocialMediaAnalysis._SocialMediaAnalysis import SocialMediaAnalysisContext
from DataAnalysis.InteractivityAnalysis.SocialMediaAnalysis._SocialMediaAnalysis import SocialMediaAnalysisContext
import jellyfish as jf
class InteractivityAnalysis:
    """aims to evaluate the interactivity and security of a website. It also contains the communication between Government and citizen
    - protocol used (http/https)
    - use of login
    - use of social media
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

    def run_interactivity_analysis_per_page(self):
        self.results_per_page = {}
        for item in self.crawlresults:
            soup = BeautifulSoup(item['html'], features='lxml')
            self.results_per_page[int(item['result_id'])] = {}

            res = self.get_login_analysis_per_page(item, soup)
            for key in res['val'].keys():
                self.results_per_page[int(res['key'])][key] = res['val'][key]

            res = self.get_online_forms_per_page(item, soup)
            for key in res['val'].keys():
                self.results_per_page[int(res['key'])][key] = res['val'][key]

            res = self.get_contact_email_per_page(item, soup)
            for key in res['val'].keys():
                self.results_per_page[int(res['key'])][key] = res['val'][key]
    def run_interactivity_analysis(self):
        status = self.get_login_analysis()
        if status != 0:
            raise 'status from InteractivityAnalysis.get_login() returned non zero'
        status = self.get_social_media_analysis()
        if status != 0:
            raise 'status from InteractivityAnalysis.get_social_media() returned non zero'
        status = self.get_online_forms()
        if status != 0:
            raise 'status from InteractivityAnalysis.get_online_forms() returned non zero'

    def valid_link_tag(self, tag) -> bool:
        if 'href' in tag.attrs.keys():
            if tag['href'].split(':')[0].lower() == 'mailto' and len(tag['href'].split(':')) > 1:
                return True
            else:
                return False
        else:
            return False

    def get_contact_email_per_page(self, item, soup=None):
        if soup is None:
            soup = BeautifulSoup(item['html'], features='lxml')
        ''' searches for email addresses on every page given'''
        self.url = self.ds.postgres.interact_postgres_df(f'select top_url from crawl where id = {self.crawl_id}').values[0][0]
        domain = self.url.split('www.')[-1].replace('.gov', '')
        self.email_addr = [re.sub(re.compile(r'.*mailto:|\?.*|&.*'), '', tag['href'])
            # (tag.get_text().strip(), tag['href'].split(':')[1])
                           for tag in soup.find_all('a', {'href':re.compile(r'mailto')})
                           if self.valid_link_tag(tag)]
        if len(self.email_addr) == 0:
            return {
            'key': item['result_id'],
            'val': {
                'emails': None,
                # 'simil': None
            }
            }
        else:
            self.email_sim = [
                (email,
                 jf.levenshtein_distance(domain, email.split('@')[1]),
                 1 - jf.jaro_similarity(domain, email.split('@')[1]),
                 jf.hamming_distance(domain, email.split('@')[1]))
                # for email in list(set(np.array(email_addresses)[:, 1]))
                for email in list(set(self.email_addr))
                if len(email) > 0 and len(email.split('@')) > 1
            ]

            #columns: mail address, levenshtein distance, inverted jaro similarity, hamming distance
            df = pd.DataFrame(self.email_sim).set_index(0)
            df_counts = pd.DataFrame(dict(Counter(self.email_addr)), index=[0]).transpose()
            df_scaled = pd.DataFrame(
                preprocessing.MinMaxScaler().fit_transform(df.values),
                columns=df.columns,
                index=df.index
            )

            self.df_final = pd.concat([df_scaled.mean(1), df_counts], axis=1)
            self.df_final.columns = ['scores', 'counts']
            self.df_final = self.df_final.sort_values(['scores', 'counts'], ascending=[True, False])

        return {
            'key': item['result_id'],
            'val': {
                'emails': ' '.join(list(self.df_final.index)),
                # 'simil': ' '.join([str(sim) for sim in self.email_sim])
            }
        }

    def get_contact_email(self) -> tuple[int, str]:
        '''
        searches for a contact email address until it finds one
        '''
        self.results['email'] = {
            'value': None,
            'emails': []
        }
        self.url = self.ds.postgres.interact_postgres_df(f'select top_url from crawl where id = {self.crawl_id}').values[0][0]
        domain = self.url.split('www.')[-1].replace('.gov', '')
        addrss = []
        email_addresses = [re.sub(re.compile(r'.*mailto:|\?.*|&.*'), '', tag['href'])
            # (tag.get_text().strip(), tag['href'].split(':')[1])
                           for item in self.crawlresults
                           for tag in BeautifulSoup(item['html'], features='lxml').find_all('a', {'href':re.compile(r'mailto')})
                           if self.valid_link_tag(tag)]
        self.email_addr = email_addresses
        #TODO could implement also only written emailaddress
        if len(email_addresses) == 0:
            return 0, 'no emails found'
        else:
            self.email_sim = [
                (email,
                 jf.levenshtein_distance(domain, email.split('@')[1]),
                 1 - jf.jaro_similarity(domain, email.split('@')[1]),
                 jf.hamming_distance(domain, email.split('@')[1]))
                # for email in list(set(np.array(email_addresses)[:, 1]))
                for email in list(set(email_addresses))
                if len(email) > 0 and len(email.split('@')) > 1
            ]
            #columns: mail address, levenshtein distance, inverted jaro similarity, hamming distance
            df = pd.DataFrame(self.email_sim).set_index(0)
            df_counts = pd.DataFrame(dict(Counter(email_addresses)), index=[0]).transpose()
            df_scaled = pd.DataFrame(
                preprocessing.MinMaxScaler().fit_transform(df.values),
                columns=df.columns,
                index=df.index
            )

            self.df_final = pd.concat([df_scaled.mean(1), df_counts], axis=1)
            self.df_final.columns = ['scores', 'counts']
            self.df_final = self.df_final.sort_values(['scores', 'counts'], ascending=[True, False])
            if self.df_final.iloc[0,0] == 0:
                self.results['email']['value'] = True
                self.results['email']['emails'] = list(self.df_final.loc[
                                                           (self.df_final.scores == 0) &
                                                           (self.df_final.counts >= self.df_final.counts.quantile(0.95))
                                                           ].index)
            else:
                self.results['email']['value'] = False






    def get_protocol_format(self):
        pass

    def get_login_analysis_per_page(self, item, soup = None):
        if soup is None:
            soup = BeautifulSoup(item['html'], features="lxml")
        self.results['login'] = {}
        # TODO implement the keywords in the mongo database
        # if False:
        #     pass
        # else:
        #     login_keywords = ['username', 'password', 'email']
        login_keywords = ['username', 'password', 'email']
        html = item['html']
        child_pw = soup.find('input', {'type': 'password'})
        if child_pw is None:
            res = {
                'key': item['result_id'],
                'val': {'has_login': False}
            }
            return res
        forms = []
        siblings = [child.get('type') for child in child_pw.find_parent('form').find_all('input')]

        if sum([tp in login_keywords for tp in siblings]) > 1:
            forms.append(siblings)

        if len(forms) > 0:
            res = {
                'key': item['result_id'],
                'val': {'has_login': True}
            }
        else:
            res = {
                'key': item['result_id'],
                'val': {'has_login': False}
            }
        return res


    def get_login_analysis(self):
        self.results['login'] = {}
        # TODO implement the keywords in the mongo database
        if False:
            pass
        else:
            login_keywords = ['username', 'password', 'email']

        if self.crawlresults is None:
            if type(self.crawl_id) == int:
                self.crawlresults = self.ds.mongo.get_results_by_crawl(self.crawl_id)
            return 1
        forms = []
        for page in self.crawlresults:
            html = page['html']
            child_pw = BeautifulSoup(html).find('input', {'type': 'password'})
            if child_pw is None:
                continue
            siblings = [child.get('type') for child in child_pw.find_parent('form').find_all('input')]

            if sum([tp in login_keywords for tp in siblings]) > 1:
                forms.append(siblings)
                if self.greedy_analysis:
                    break
        if len(forms) > 0:
            self.results['login']['score'] = True
        return 0
            # [[inp.get('type') for inp in pw.find_parent('form').find_all('input')] for pw in BeautifulSoup(html).find('input', {'type': 'password'})]



    def get_social_media_analysis(self) -> int:
        with SocialMediaAnalysisContext(crawlresults=self.crawlresults) as sma:
            sma.analyze()
            self.results['socialmedia_score'] = {
                'score': sma.social_media_score,
                'facebook_account': sma.social_media_dict['facebook']['account'],
                'twitter_account': sma.social_media_dict['twitter']['account'],
                'instagram_account': sma.social_media_dict['instagram']['account'],
                'youtube_account': sma.social_media_dict['youtube']['account']
            }
        return 0

    def get_online_forms_per_page(self, item, soup=None):
        if soup is None:
            soup = BeautifulSoup(item['html'], features="lxml")
        input_tags = soup.find_all(['input', 'textarea'], type='text')
        input_name = [tag.get('name') for tag in input_tags]
        input_type = [tag.get('type') for tag in input_tags]
        url = self.ds.postgres.interact_postgres(f'select url from crawl_result where id = {item["result_id"]}')
        return {
            'key': item['result_id'],
            'val': {
                'n_inputs': len(input_tags),
                'input_names': ' '.join(input_name),
                'input_type':  ' '.join(input_type),
                'url': url
            }
            }


    def get_online_forms(self):
        res = []
        for page in self.crawlresults:
            soup = BeautifulSoup(page['html'])
            input_tags = soup.find_all(['input', 'textarea'], type='text')
            nr_tags = len(input_tags)
            url = self.ds.postgres.interact_postgres(f'select url from crawl_result where id = {page["result_id"]}')
            res.append((input_tags, nr_tags, url))
        return res


class InteractivityAnalysisContext:
    def __init__(self, **kwargs):
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
    def __enter__(self) -> InteractivityAnalysis:
        self._ia = InteractivityAnalysis(crawlresults=self.crawlresults)
        return self._ia

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self._ia

if __name__ == '__main__':
    # import numpy as np
    # # crawl_id = 4245
    # crawl_id = 4249
    # ta = InteractivityAnalysis(crawl_id=crawl_id)
    # res = ta.get_online_forms()
    # nr_inputs = [page[1] for page in res]
    # pages_q = [page for page in res if page[1] > np.quantile(nr_inputs, q=0.95)]
    # from DataAnalysis.InteractivityAnalysis._InteractivityAnalysis import InteractivityAnalysis
    from pprint import pprint
    crawl_id = 2307 #Bern
    crawl_id = 4249 #Hittnau
    crawl_id = 4251 #Bern
    crawl_id = 4247 #Uster
    crawl_id = 4252 #Zuerich
    ia = InteractivityAnalysis(crawl_id=4249)
    ia.run_interactivity_analysis_per_page()
    df = pd.DataFrame(ia.results_per_page).transpose()
    # ia.get_contact_email()
    # pprint(ia.results)
    # crawl_ids = [4249, 4251, 4247, 4252]
    print(df)