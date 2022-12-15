import os
import pandas as pd
import numpy as np
from DataSourceSlim import DataSourceSlim
from enum import Enum
from bs4 import BeautifulSoup
import jellyfish as jf
from sklearn import preprocessing
from collections import Counter
from progressbar import progressbar
from bson.objectid import ObjectId

VALID_EMAIL_ANALYSIS_OPTIONS = {'text': 0, 'link': 1}


class EmailAnalysisMode(Enum):
    SINGLE = 0
    ALL = 1
    MISSING_EMAILS = 2
    NEVER_ANALYZED = 3


def valid_email(tag):
    if 'href' in tag.attrs.keys():
        if tag['href'].split(':')[0].lower() == 'mailto' and len(tag['href'].split(':')) > 1:
            # print(tag.get_text().strip(), tag['href'])
            return True
        else:
            return False
    else:
        return False


class EmailAnalysis:
    def __init__(self, mode: int, **kwargs):
        if 'verbose' in kwargs:
            self.verbose = bool(kwargs['verbose'])
        else:
            self.verbose = False
        self.sorted_emails = None
        self.email_list = None
        self.domain = None
        self.crawl_id = None
        self.page_list = None
        self.ds = DataSourceSlim()
        self.mode = EmailAnalysisMode(mode)
        self.get_kwargs(kwargs)

        # self.run_analysis()

    def get_kwargs(self, kwargs):
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']

    def get_data(self, **kwargs):
        force=False
        if 'force' in list(kwargs.keys()):
            force = kwargs['force']
        if self.page_list is None or force:
            self.page_list = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]
        top_url = self.ds.postgres.interact_postgres(f'select top_url from crawl where id = {self.crawl_id};')[0][0]
        url_split = top_url.split('www.')
        self.domain = url_split[1] if len(url_split) > 1 else url_split[0]
        self.email_list = [(tag.get_text().strip(), tag['href'].split(':')[1])
                           for item in self.page_list
                           for tag in BeautifulSoup(item['html'], features='lxml').find_all('a') if valid_email(tag)]

    def get_email_similarity(self, similarty_of: str = 'link') -> tuple:
        if len(self.email_list) == 0:
            return (None, {'emails_descending': []})
        if similarty_of not in VALID_EMAIL_ANALYSIS_OPTIONS:
            raise 'No valid mode for email address analysis'
        mode = 1 if similarty_of == 'link' else 0
        email_dict = dict(Counter([item[mode] for item in self.email_list]))
        email_index = list(email_dict.keys())

        email_similarity = [(email, email_dict[email],
                             jf.levenshtein_distance(self.domain, email.split('@')[1]),
                             1 - jf.jaro_similarity(self.domain, email.split('@')[1]),
                             jf.hamming_distance(self.domain, email.split('@')[1]))
                            for email in email_index if
                            len(email) > 0 and len(email.split('@')) > 1]

        self.df_sim = pd.DataFrame(email_similarity, columns=['email', 'count', 'lev', 'jar', 'ham']).set_index('email')
        ar_sim = self.df_sim.values
        if ar_sim.shape[0] == 0:
            return (None, {'emails_descending': []})
        mean_similarity_score = preprocessing.MinMaxScaler().fit_transform(ar_sim[:, 1:]).mean(axis=1)
        counts = self.df_sim['count'].values
        suggested_email_desc = pd.DataFrame(
            {
                'count': list(counts),
                'similarity_score': list(mean_similarity_score),
                'email': list(self.df_sim.index)
            },
            index=list(range(self.df_sim.shape[0]))
        )
        df_agg = suggested_email_desc.groupby(['similarity_score', 'email']).agg({'count': sum})
        gen = df_agg['count'].groupby('similarity_score', group_keys=False)
        self.sorted_emails = gen.apply(lambda x: x.sort_values(ascending=False))
        most_relevant_mail = self.sorted_emails.index[0][1]
        return most_relevant_mail, {'emails_descending': [(mail, float(score), int(self.sorted_emails[score][mail]))
                                                          for score, mail in self.sorted_emails.index]}

    def select_crawl_ids(self):
        pass

    def run_analysis(self):
        pass

    def process_municipalities(self, mun_df: pd.DataFrame, **kwargs):
        if self.mode != EmailAnalysisMode(0):
            force = True
        else:
            force = False
        for i in progressbar(mun_df.index):
            mun_id = int(mun_df.loc[i].id)
            mun_name = mun_df.loc[i].name_de
            mun_url = mun_df.loc[i].url
            res = self.ds.postgres.interact_postgres(
                f'''
                SELECT crawl_id, mongo_analysis_id 
                FROM digilog.digilog.crawl_analysis 
                WHERE crawl_analysis.log_gov_id = {mun_id} 
                ORDER BY crawl_analysis.crawl_id DESC 
                LIMIT 1;
                '''
            )
            if len(res) == 1:
                self.crawl_id, mongo_analysis_id = res[0]
                self.get_data(force=force)
                mun_email, mun_email_ranking = self.get_email_similarity()
                self.ds.mongo.db.simpleanalysis.update_one(
                    {'_id': ObjectId(mongo_analysis_id)},
                    {'$set': {
                        'email_similarityscore_occurence_list': mun_email_ranking['emails_descending'],
                        'email_contact': mun_email
                    }
                    }
                )
            else:
                self.crawl_id, mongo_analysis_id,mun_email = None, None, None

            self.ds.postgres.insert_email_address(self.crawl_id, mun_id, mun_email)
            if self.verbose:
                print(f'\n{mun_name},\t{mun_url}, crawl_id: {self.crawl_id},\t mongo_analysis_id: {mongo_analysis_id}\n')

            # TODO implementation of email analysis and insertion into database (mongo as well)



    def run_cases(self, municipality_min: int = None, municipality_max:int = None):
        if self.mode == EmailAnalysisMode(0): #single
            self.email_contact, self.email_contact_list = self.get_email_similarity()

        elif self.mode == EmailAnalysisMode(1):
            mun_df = self.ds.postgres.interact_postgres_df(
                '''
                select id, name_de, url from digilog.digilog.municipality;
                '''
            )
            self.process_municipalities(mun_df=mun_df)

        elif self.mode == EmailAnalysisMode(2):
            mun_df = self.ds.postgres.interact_postgres_df(
                f'''
                select id, name_de, url from digilog.digilog.municipality where id >= {municipality_min} and id <= {municipality_max};
                '''
            )
            self.process_municipalities(mun_df=mun_df)
        elif self.mode == EmailAnalysisMode(3):
            pass



if __name__ == '__main__':
    # ea = EmailAnalysis(0, crawl_id=2117)
    # ea.get_data()
    # email, email_list = ea.get_email_similarity()
    ea = EmailAnalysis(mode=1, verbose=False)
    ea.run_cases()
