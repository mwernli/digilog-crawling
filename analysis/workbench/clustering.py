import pandas as pd
from bson.objectid import ObjectId
from DataSourceSlim import DataSourceSlim
from progressbar import progressbar
from bs4 import BeautifulSoup
import numpy as np
from sklearn.cluster import KMeans, SpectralClustering, DBSCAN, MeanShift
from tmtoolkit.corpus import Corpus, tokens_table, lemmatize, to_lowercase, dtm
from tmtoolkit.bow.bow_stats import tfidf, sorted_terms_table
from collections import Counter
import matplotlib.pyplot as plt
import os
import spacy
from string import punctuation
import re
from datetime import datetime

nlp = spacy.load('de_core_news_sm')
CRAWL_IDS = [4249, 4251, 4247, 4252]

class SiteAnalysis:
    def __init__(self):
        self.df_features = None
        self.cluster_dict = None
        self.text_dict = None
        self.df_text = None
        self.ds = DataSourceSlim()
        self.df_crawlresults = None

    def read_crawls(self, crawl_ids = None):
        if crawl_ids is None:
            crawl_ids = CRAWL_IDS

        for crawl in crawl_ids:
            if self.df_crawlresults is None:
                self.df_crawlresults = self.ds.postgres.interact_postgres_df(f"select * from crawl_result where ((crawl_id = {crawl}) and (mongo_id is not null))").set_index('id')
            else:
                self.df_crawlresults = pd.concat(
                    [
                        self.df_crawlresults,
                        self.ds.postgres.interact_postgres_df(f'select * from crawl_result where ((crawl_id = {crawl}) and (mongo_id is not null))').set_index('id')
                    ], axis=0
                )
    def read_hittnau(self):
        pass


    def read_crawls_html(self):
        if self.df_crawlresults is None:
            print('no crawl results')
            return 1
        # self.html_list = [{item['result_id']: item['html']} for item in self.ds.mongo.db.simpleresults.find({'_id': {'$in': [ObjectId(id) for id in self.df_crawlresults.mongo_id.values]}})]
        self.text_dict = {}
        self.cluster_dict = {}
        for id in progressbar(self.df_crawlresults.mongo_id.values):
            item = self.ds.mongo.db.simpleresults.find_one({'_id': ObjectId(id)})
            # html_list[item['result_id']]= {
            #         'crawl_id': item['crawl_id'],
            #         'html': item['html']
            #     }

            self.cluster_dict[item['result_id']], self.text_dict[item['result_id']] = self.feature_engineering(item)

        # self.df_features = pd.DataFrame(self.html_dict, index=list(range(len(self.html_dict)))).set_index('result_id')
        self.df_features = pd.DataFrame(self.cluster_dict).transpose().set_index(['crawl_id', 'result_id'])
        self.df_text = pd.DataFrame(self.text_dict).transpose().set_index(['crawl_id', 'result_id'])
        self.df_features.to_csv('../data/cluster_data_example.csv')

    def feature_engineering(self, item) -> tuple:
        soup = BeautifulSoup(item['html'])
        n_inputs = len(soup.find_all('input'))
        forms = soup.find_all('form')
        n_inputs_per_form = np.array([len(form.find_all('input')) for form in forms])
        text = re.sub(re.compile(r'\n+|\s+'), ' ', soup.get_text())
        # hotwords = get_hot_words()
        l_text = len(text)
        n_links = len(soup.find_all('a'))
        divs = soup.find_all('div')
        n_children_divs = [len([child for child in tag.children]) for tag in divs]

        if len(n_children_divs) == 0:
            divs_max_children = 0
            divs_mean_children = 0
            divs_median_children = 0
        else:
            divs_max_children = np.max(n_children_divs)
            divs_mean_children = np.mean(n_children_divs)
            divs_median_children = np.median(n_children_divs)

        n_h1 = len(soup.find_all('h1'))
        n_h2 = len(soup.find_all('h2'))
        return ({
            'crawl_id': item['crawl_id'],
            'result_id': item['result_id'],
            'n_inputs': n_inputs,
            'n_inputs_form_1': (n_inputs_per_form == 1).sum(),
            'n_inputs_form_2_3': ((n_inputs_per_form > 1) & (n_inputs_per_form < 4)).sum(),
            'n_inputs_form_4_': (n_inputs_per_form > 3).sum(),
            'l_text': l_text,
            'n_links': n_links,
            'children_max': divs_max_children,
            'children_mean': divs_mean_children,
            'children_median': divs_median_children,
            'n_h1': n_h1,
            'n_h2': n_h2
        }, {
            'crawl_id': item['crawl_id'],
            'result_id': item['result_id'],
            'text': text
        })

def get_hot_words(text):
    result = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN']
    doc = nlp(text)
    for token in doc:
        if (token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if (token.pos_ in pos_tag):
            result.append(token.text)
    return result

def dbscan(df):
    dbscan = DBSCAN()
    res = dbscan.fit_predict(df)
    df_clusters = pd.DataFrame(Counter(res), index=['cluster']).transpose()
    df_clusters.cluster.plot.bar()
    plt.title('dbscan barplot')
    plt.show()
    df_clusters.plot.hist()
    plt.title('dbscan hist')
    plt.show()
    print(f'===\nDBSCAN:\nn_classes: {df_clusters.shape[0]}\n===')
    return res

def kmeans_range(df, K=20):
    distortions = []
    for k in progressbar(range(1,K)):
        model = KMeans(n_clusters=k)
        model.fit(df)
        distortions.append(model.inertia_)
    res_df = pd.DataFrame([list(range(1,K)), distortions]).transpose()
    res_df.columns = ['k', 'distortions']
    df = res_df.set_index('k')
    df.distortions.plot.line()
    plt.title('kmeans')
    plt.show()
    return df
def kmeans(df, k=10):
    model = KMeans(n_clusters=k)
    return model.fit_predict(df)


def tf_idf(text_dict, clean = True):
    start0 = datetime.now()
    nlp = spacy.load('de_core_news_sm')
    text_dict_processed = {}
    for res_id in progressbar(text_dict.keys()):
        if clean:
            text_dict_processed[res_id] = ' '.join([
                token.text.strip() for token in nlp(text_dict[res_id])
                if not token.text.strip() in nlp.Defaults.stop_words
                   and not token.is_punct
                   and not token.is_space
                   and not token.like_num
                   and not token.is_digit
                   and not token.pos_ in ['X', 'SPACE', 'SYM']
                   and not len(token.text) <= 3
                   and not bool(re.search(re.compile('\d\d+'), token.text))
                ])
        else:
            text_dict_processed[res_id] = text_dict[res_id]
    end = datetime.now() - start0
    print(f'cleaning with nlp: {end.seconds/60} mins')
    # load built-in sample dataset and use 4 worker processes
    start = datetime.now()
    # corp = Corpus.from_builtin_corpus('en-News100', max_workers=4)
    corp = Corpus(text_dict_processed, language='de')
    end = datetime.now() - start
    print(f'create corpus: {end.seconds/60} mins')

    # investigate corpus as dataframe
    start = datetime.now()
    toktbl = tokens_table(corp)
    end = datetime.now() -start
    print(f'create token table: {end.seconds/60} mins')
    # print(toktbl)

    # apply some text normalization
    start = datetime.now()
    lemmatize(corp)
    end = datetime.now() -start
    print(f'lemmatice corpus: {end.seconds/60} mins')

    start = datetime.now()
    to_lowercase(corp)
    end = datetime.now() -start
    print(f'lower case corpus: {end.seconds/60} mins')
    # build sparse document-token matrix (DTM)
    # document labels identify rows, vocabulary tokens identify columns
    start = datetime.now()
    mat, doc_labels, vocab = dtm(corp, return_doc_labels=True, return_vocab=True)
    end = datetime.now() -start
    print(f'build sparse document-token matrix (DTM): {end.seconds/60} mins')
    # apply tf-idf transformation to DTM
    # operation is applied on sparse matrix and uses few memory
    start = datetime.now()
    tfidf_mat = tfidf(mat)
    end = datetime.now() -start
    print(f'apply tf-idf transformation to DTM: {end.seconds/60} mins')
    # show top 5 tokens per document ranked by tf-idf
    start = datetime.now()
    top_tokens = sorted_terms_table(tfidf_mat, vocab, doc_labels, top_n=10)
    end = datetime.now() -start
    print(f'show top 5 tokens per document ranked by tf-idf: {end.seconds/60} mins')
    # print(top_tokens)
    print(f'time for all: {(datetime.now() - start0)/60} min')
    return top_tokens





# https://www.youtube.com/watch?v=l2CcR9zeKwc
CRAWL_IDS = [4249, 4251, 4247, 4252]
if __name__ == '__main__':
    crawl_id = 2307 #Bern
    crawl_id = 4251 #Bern
    crawl_id = 4247 #Uster
    crawl_id = 4252 #Zuerich
    crawl_id = 4249 #Hittnau

    start__0 = datetime.now()
    sa = SiteAnalysis()
    # sa.read_crawls(CRAWL_IDS)
    sa.read_crawls([crawl_id])
    sa.read_crawls_html()
    df_transformed = np.sqrt(sa.df_features)
    df_text = sa.df_text
    text_dict = sa.df_text.loc[crawl_id].to_dict()['text']
    # print(sa.df_crawlresults)
    # res_dbscan = dbscan(df_transformed)
    # df_elbow = kmeans_range(df_transformed)
    # res_kmeans= kmeans(df_transformed)
    # df_clusters = pd.concat([sa.df_crawlresults.crawl_id, pd.DataFrame(
    #     {
    #         'kmeans': res_kmeans,
    #         'dbscan': res_dbscan
    #     }, index=df_transformed.index
    # )], axis=1)
    top_tokens = tf_idf(text_dict)
    top_tokens_uncleaned = tf_idf(text_dict, clean=False)
    # df_text.set_index('result_id')
    df = pd.concat([df_text.droplevel('crawl_id'), sa.df_crawlresults], axis=1)
    df['tokens'] = None
    for result_id in progressbar(top_tokens.index.get_level_values('doc')):
        df.loc[result_id, 'tokens'] = '  '.join(list(top_tokens.loc[result_id].token.values))
        df.loc[result_id, 'token_values'] = '  '.join(list([str(item) for item in top_tokens.loc[result_id].value.values]))

    for result_id in progressbar(top_tokens_uncleaned.index.get_level_values('doc')):
        df.loc[result_id, 'tokens_uncleaned'] = '  '.join(list(top_tokens_uncleaned.loc[result_id].token.values))
        df.loc[result_id, 'token_values_uncleaned'] = '  '.join(list([str(item) for item in top_tokens_uncleaned.loc[result_id].value.values]))

    # top_tokens.loc[94910398]
    df_slim = df.dropna()[['url', 'link_text', 'tokens', 'token_values', 'tokens_uncleaned', 'token_values_uncleaned']]
    # df_slim.to_csv('../data/df_tf_idf.csv')
    df_slim.to_csv('../data/hittnau/df_hittnau_tokens.csv')
    end__0 = datetime.now() - start__0
    mins = end__0.seconds
    os.system(f'spd-say "your program has finished within {round(mins/60, 1)} minutes"')
    print(f"your program has finished within {round(mins/60, 1)} minutes")

