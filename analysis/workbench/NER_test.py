import re

import pandas as pd
import os
import numpy as np
import sklearn.metrics

from DataSourceSlim import DataSourceSlim
from bs4 import BeautifulSoup
import time
import spacy
from collections import Counter
from pprint import pprint
import classy_classification
from pathlib import Path
from spacy import displacy
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, accuracy_score, precision_recall_fscore_support
import matplotlib.pyplot as plt
import seaborn as sns
from progressbar import progressbar
from tqdm import tqdm
nlp = spacy.load('de_core_news_sm')



ds = DataSourceSlim()
def get_results_df(crawl_id):
    start = time.time()
    # mongo_res = [(res['result_id'], res['html'], BeautifulSoup(res['html']).getText().replace('\n', ' ').replace('   ', ''))for res in ds.mongo.db.simpleresults.find({'crawl_id':crawl_id})]
    mongo_res = [(res['result_id'], res['html'])for res in ds.mongo.db.simpleresults.find({'crawl_id':crawl_id})]
    postg_df = ds.postgres.interact_postgres_df(f'select * from crawl_result where crawl_id={crawl_id}').set_index('id')
    postg_df = postg_df[[item is not None for item in postg_df.mongo_id.values]]
    # mongo_df = pd.DataFrame(mongo_res, columns=['id', 'html', 'text']).set_index('id')
    mongo_df = pd.DataFrame(mongo_res, columns=['id', 'html']).set_index('id')

    for html in mongo_df.html.values:
        text = clean_html(html)

    # mongo_df['text'] = [BeautifulSoup(page).getText() for page in mongo_df['html'].values]
    df = pd.concat([postg_df, mongo_df], axis=1)
    delta = time.time() - start
    print('data loaded in {mins} min(s) and {secs} seconds'.format(mins=int(delta/60), secs=round(delta%60, 2)) )
    return df

def clean_html(html):
    soup = BeautifulSoup()
    res = [(len(tag.text), re.sub(' +', ' ', tag.text.replace('\n', ' ').replace('\t', '')), tag.name) for tag in
           soup.find_all()]
    df_res = pd.DataFrame(res, columns=['length', 'text', 'tag'])


def get_fuzzy_matched_indexes(df, services:list = None):

    nlp = spacy.blank('de')
    # lemmatizer = nlp.add_pipe('lemmatizer', config={'mode': 'lookup'})
    # try:
    #     nlp.initialize()
    # except ValueError:
    #     print('no lookup table found')
    # nlp = spacy.load('de_core_news_sm', disable=['ner'])
    if services is None:
        services = ['Dienst', 'Schalter', 'Umzug', 'Wegzug', 'Zuzug']
    informations = ['information', 'info', 'aktuell']
    gesetz = ['artikel', 'paragraph', 'gesetz']
    online = ['Online']
    ruler = nlp.add_pipe('entity_ruler')
    pattern_information = {'pattern': [{'LOWER': {'FUZZY': info.lower()}} for info in informations], 'label': 'INFORMATION'}
    pattern_services = {'pattern': [{'LOWER': {'FUZZY': keyword.lower()}} for keyword in services], 'label': 'SERVICE'}
    pattern_online = {'pattern': [{'LOWER': {'FUZZY': keyword.lower()}} for keyword in online], 'label': 'DIGITAL'}
    ruler.add_patterns([ pattern_services, pattern_information, pattern_online])
    df['keywords'] = None
    df['entities'] = None
    ents = []
    for id, row in df.iterrows():
        # ents_.append((id, [(tok.ent_id_, tok.text) for tok in nlp((row.url.replace('/', ' ').replace('.', ' ').replace('-', ' '))) if tok.ent_id_ != '']))
        ent = [(tok.ent_type_, tok.text) for tok in nlp(re.sub(r"[,.;@#?!&$/-]+\ *", " ", row.url.lower())) if tok.ent_type_ != '']
        if len(ent) > 0:
            ents.append((id, row.url, row.link_text, ent))
        # ents_.append((id, [(tok.ent_id_, tok.text) for tok in nlp(row.link_text.lower()) if tok.ent_id_ != '']))
    # doc = nlp('Hier bekommen Sie Ihre INormationen zu den jewieligen Online Diensten.')
    # svg = displacy.render(doc, style='ent')
    # outputpath = Path('../data/images/sents.html')
    # outputpath.open('w', encoding='utf-8').write(svg)

def rule_based_matching(df, services:list = None, classification_url:bool = True):
    if not classification_url:
        if services is None:
            services = ['Dienst', 'Schalter', 'Umzug', 'Wegzug', 'Zuzug', 'login', 'service', 'ausfüllen', 'online', 'Anmeld', 'Bewilligung', 'Ausweis', 'Anfrage']
        informations = ['information', 'info', 'aktuell', 'Mitteilung', 'Beschlüsse', 'Organisation', 'Projekt', 'Fakten', 'Auskunft', 'Auskünfte']
        gesetz = ['artikel', 'paragraph', 'gesetz', 'Verordnung', 'ordnung', 'Verfügung', 'Bestimmung', 'Reglement']
        # online = ['Online']
        inserate = ['arbeitenundausbildung', 'offenestellen']
        gesellschaft_kultur_sport = ['Kultur', 'Sport', 'Kunst', 'Bibliothek', 'Verein', 'Senior', 'Jugend']
        politik_verwaltung = ['aemter', 'Kontakt', 'Amt', 'Departement']
    else:
        # classification url
        if services is None:
            services = ['Online', 'Schalter', 'Dienstleistungen']
        politik_verwaltung = ['Verwaltungsleitung', 'aemter', 'Kontaktformular', 'Amt', 'Departemente', 'unterinstanzen',
                              'personenregister', 'gemeinderat', 'legislative', 'exekutive',
                              'behoerden', 'partei', 'finanzen', 'abstimmung', 'politik', 'sitzung']
        inserate = ['arbeitenundausbildung', 'offenestellen']
        informations = ['publikationen', 'aktuelles', 'informationen', 'beschluesse', 'mitteilungen', 'anlaesse', 'aktuell']
        gesetz = ['gesetzessammlung', 'gesetzteskapitel', 'gesetz']
        gesellschaft_kultur_sport = ['Verein', 'Kultur', 'Sport', 'Alter', 'Familie', 'Kinder', 'Jugend', 'Kunst', 'bibliothek', 'Gesellschaft',
                                     'umwelt', 'wohnen', 'arbeiten', 'tourismus']

    class_dict = {
        'SERVICES': services,
        # 'INFORMATIONS': informations,
        # 'LAWS': gesetz,
        # 'GESELLSCHAFT_KULTUR_SPORT': gesellschaft_kultur_sport,
        # 'INSERATE': inserate,
        # 'VERWALTUNG': politik_verwaltung
    }
    res_dict = {}
    for id, row in df.iterrows():
        if classification_url:
            res = [(keyword, clss)  for clss in list(class_dict.keys()) for keyword in class_dict[clss] if re.search(keyword.lower(), row.url.lower())]
        else:
            res = [(keyword, clss)  for clss in list(class_dict.keys()) for keyword in class_dict[clss] if re.search(keyword.lower(), row.text.lower())]
        res_dict[id] = {
            'url': row.url,
            'res': res
        }
    res_df = pd.DataFrame(res_dict).transpose()
    df.loc[:, 'clss'] = None
    res_df_pos = res_df[[len(val)>0 for val in res_df.res]]
    res_df_pos.loc[:,'clss'] = None
    res_df_pos.loc[:, 'clss_mst_cmmn'] = None
    res_df_pos.loc[:, 'matches'] = res_df_pos.res
    res_df_pos_copy = res_df_pos.copy()
    for i in res_df_pos.index:

        count_dict = Counter([clss for key, clss in res_df_pos.loc[i].res])
        dict_vals = np.array(list(count_dict.values()))
        dict_keys = list(count_dict.keys())
        res_df_pos_copy.loc[i, 'clss'] = [(key, count_dict[key]/dict_vals.sum()) for key in dict_keys]
        res_df_pos_copy.loc[i, 'clss_mst_cmmn'] = count_dict.most_common(1)[0][0]
    return res_df_pos_copy

def balanced_sample(df_in, n_min=None, seed=0):
    count_treshold = 10
    np.random.seed(seed)
    df = df_in.copy()
    count_df = pd.DataFrame(dict(Counter(df.clss)), index=['counts']).transpose()
    print(f'Classes {list(count_df[count_df.counts < count_treshold].index)} are not taken in account')
    df = df_in[[clss in list(set(count_df[count_df.counts > count_treshold].index)) for clss in progressbar(df_in.clss)]]
    if n_min is None:
        n_min = Counter(df.clss).most_common()[-1][1]
    inds = []
    print('creating balanced dataset...')
    for clss in progressbar(list(set(df.clss.values))):
        sub_df = df[df.clss == clss]
        inds.extend(np.random.choice(sub_df.index, size=n_min, replace=False))
    return df.loc[inds]

def clean_data(df):
    df_copy = df.copy()
    print('cleaning data...')
    for i, row in progressbar(df.iterrows()):
        a =  re.sub(' +', ' ', row.text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' '))
        # a =  re.sub(' +', ' ', a.replace('/', ' ').replace('|', ' '))
        b = re.sub('\d\d.\d\d.\d\d\d\d', '', a)
        df_copy.loc[i, 'text'] = b
    return df_copy

def clean_url(url:str, level:int=1):
    if level==0:
        return url.replace('/', ' ').replace('.', ' ')
    elif level==1:
        return url.replace('/', ' ').replace('.', ' ').replace('?', ' ' ).replace('&', ' ')
    elif level==2:
        return re.sub('\d+', '', url.replace('/', ' ').replace('.', ' ').replace('?', ' ' ).replace('&', ' ').replace('www', ''))
    elif level==3:
        return re.sub('\d+', '', url.replace('/', ' ').replace('.', ' ').replace('?', ' ' ).replace('&', ' ').replace('www', '').replace('-', ' '))
    else:
        return url


def bert_model_data(X, y, type:str, n_max:int=1000, clean_level:int=1):
    df = pd.concat([X,y], axis=1)
    if type == 'text':
        pass
    data = {}
    # print('prepairing bert model')
    for clss in list(set(df.clss)):
        # data[clss] = [sent for text in df[df.clss == clss].text for sent in nlp(text).sents]
        if type == 'text':
            data[clss] = [text for text in df[df.clss == clss].text]
        elif type == 'url':
            if df[df.clss == clss].shape[0] > n_max:
                data[clss] = [clean_url(url=url, level=clean_level) for i, url in enumerate(df[df.clss == clss].url) if i <= n_max]
            else:
                data[clss] = [clean_url(url=url, level=clean_level)for url in df[df.clss == clss].url]
        else:
            print('no valid type')

    return data


def hyperparameter_optimization(X_train, X_test, y_train, y_test, n_max_list=None, cleaning_level_list=None):
    if cleaning_level_list is None:
        cleaning_level_list = list(range(4))
    if n_max_list is None:
        n_max_list = [10, 30, 50, 100, 200]
    res_dict = {}
    ind = 0
    tmp_df = pd.read_csv('../data/URL_NER_test_1.csv', index_col=0)
    param_grid = []
    for i, row in tmp_df.iterrows():
        res_dict[ind] = {}
        for key in tmp_df.columns:
            res_dict[ind][key] = tmp_df.loc[i, key]
        ind += 1
    for n_max in n_max_list:
        for level in cleaning_level_list:
            mask = [(row.n_max == n_max and row.cleaning_level == level) for i, row in tmp_df.iterrows()]
            if any(mask):
                continue
            else:
                param_grid.append((n_max, level))


    for n_max, level in tqdm(param_grid):
            data = bert_model_data(X_train, y_train, type='url', n_max=n_max, clean_level=level)
            nlp_categorizer = spacy.blank('en')
            # nlp_categorizer = spacy.load('de_core_news_md')
            # print('adding pipe and training pipe...')
            nlp_categorizer.add_pipe(
                "text_categorizer",
                config={
                    "data": data,
                    "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                    # 'model': 'spacy',
                    "device": "gpu"
                }
            )
            # print('...training finshed')

            test_res = [nlp_categorizer(clean_url(txt))._.cats for txt in X_test.url]
            df_test = pd.DataFrame(test_res, index=y_test.index)
            df_test_Xy = pd.concat([df_test, y_test], axis=1)
            classnames = ['NO CLASS', 'SERVICES']
            df_test_Xy.loc[:, 'clss_pred'] = df_test_Xy.loc[:, classnames].transpose().idxmax()


            cm = confusion_matrix(df_test_Xy.clss, df_test_Xy.clss_pred, labels=classnames)
            cf = classification_report(df_test_Xy.clss, df_test_Xy.clss_pred, labels=classnames)
            # disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classnames)
            # disp.plot()
            # plt.show()
            prec, rec, f1, sup = precision_recall_fscore_support(df_test_Xy.clss, df_test_Xy.clss_pred, average='weighted')
            res_dict[ind] = {
                'n_max': n_max,
                'cleaning_level': level,
                'confusion_matrix': cm,
                'classification_report': cf,
                'acc': accuracy_score(df_test_Xy.clss, df_test_Xy.clss_pred),
                'prec_w': prec,
                'rec_w': rec,
                'f1_w': f1
            }
            prec, rec, f1, sup = precision_recall_fscore_support(df_test_Xy.clss, df_test_Xy.clss_pred, average=None)
            res_dict[ind]['prec'] = prec
            res_dict[ind]['rec'] = rec
            res_dict[ind]['f1'] = f1
            res_dict[ind]['sup'] = sup

            ind += 1
            tmp_df = pd.DataFrame(res_dict).transpose()
            tmp_df.to_csv('../data/URL_NER_test_1.csv')
    return res_dict


optimize_params = True
if __name__ == '__main__':
    if os.path.exists('../data/uster_4247.csv'):
        df = pd.read_csv('../data/uster_4247.csv', index_col=0)
    else:
        df = get_results_df(4247)
    df_pos = rule_based_matching(df=df)
    df_merged = df.copy()
    df_merged.loc[:, 'clss'] = 'NO CLASS'
    df_merged.loc[df_pos.index, 'clss'] = df_pos.clss_mst_cmmn

    # all swiss urls
    df_crres = ds.postgres.interact_postgres_df('select * from crawl_result')
    df_crres = df_crres[[item != True for item in df_crres.url.isna()]]
    df_crres_with_text = df_crres[[item != True for item in df_crres.mongo_id.isna()]]
    df_crres_pos = rule_based_matching(df_crres_with_text, classification_url=True)
    df_all = df_crres_with_text.copy()
    df_all.loc[:,['clss']] = 'NO CLASS'
    df_all.loc[df_crres_pos.index, 'clss'] = df_crres_pos.clss_mst_cmmn
    #
    #balance Data
    # df_balanced = balanced_sample(df_merged)
    # df_train =  clean_data(df_balanced)
    df_bal = balanced_sample(df_all)
    X_train, X_test, y_train, y_test = train_test_split(df_bal.iloc[:,:-1], df_bal.iloc[:,-1])
    if optimize_params:
        params_dict = hyperparameter_optimization(
            X_train, X_test, y_train, y_test,
            n_max_list=[50, 100, 200, 250, 300, 400, 450, 500, 600],
            cleaning_level_list=list(range(4)))
        tmp_df = pd.read_csv('../data/URL_NER_test_1.csv', index_col=0)
        plot_df = tmp_df.loc[tmp_df.n_max < 700]
        sns.lineplot(data=plot_df, x='n_max', y='acc', hue='cleaning_level')
        plt.show()
    else:
        data = bert_model_data(X_train, y_train, type='url', n_max=5)
        nlp_categorizer = spacy.blank('en')
        # nlp_categorizer = spacy.load('de_core_news_md')
        print('adding pipe and training pipe...')
        nlp_categorizer.add_pipe(
            "text_categorizer",
            config={
                "data": data,
                "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                # 'model': 'spacy',
                "device": "gpu"
            }
        )
        print('...training finshed')
        # pd.set_option('display.max_rows', df_merged.shape[0]+1)
        # print(df_merged.loc[df_merged.clss == 'NO CLASS', ['url', 'clss']])
        text = df_merged.loc[94431684].text     # www.uster.ch/wanderwege  NO CLASS
        texts_no_cl = df_merged.loc[94431684].url.replace('/', ' ').replace('.', ' ')     # www.uster.ch/wanderwege  NO CLASS
        print('\nNO CLASS')
        pprint(nlp_categorizer(texts_no_cl)._.cats)
        text = df_merged.loc[94480057].text     # www.uster.ch/online-schalter/17829/detail  SERVICES
        text_serv = df_merged.loc[94480057].url.replace('/', ' ').replace('.', ' ')      # www.uster.ch/online-schalter/17829/detail  SERVICES
        print('\nSERVICES')
        pprint(nlp_categorizer(text_serv)._.cats)


        test_res = [nlp_categorizer(clean_url(txt))._.cats for txt in progressbar(X_test.url)]
        df_test = pd.DataFrame(test_res, index=y_test.index)
        df_test_Xy = pd.concat([df_test, y_test], axis=1)
        classnames = ['NO CLASS', 'SERVICES']
        df_test_Xy.loc[:,'clss_pred'] = df_test_Xy.loc[:, classnames].transpose().idxmax()

        cm = confusion_matrix(df_test_Xy.clss, df_test_Xy.clss_pred, labels=classnames)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classnames)
        disp.plot()
        plt.show()

        print('\nTest Hittnau')
        print('\nSERVICES')
        # text_serv = 'https://www.hittnau.ch/online-schalter/6627/detail'.replace('/', ' ').replace('.', ' ')
        text_serv = clean_url('https://www.hittnau.ch/online-schalter/6627/detail')
        pprint(nlp_categorizer(text_serv)._.cats)

        print('\nTest Hittnau')
        print('\nNO CLASS')
        # texts_no_cl = 'https://www.hittnau.ch/lebenssituationen/45704'.replace('/', ' ').replace('.', ' ')
        texts_no_cl = clean_url('https://www.hittnau.ch/lebenssituationen/45704')
        pprint(nlp_categorizer(texts_no_cl)._.cats)
