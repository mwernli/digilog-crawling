from DataSourceSlim import DataSourceSlim
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint

def plot_counts(df):
    plt.bar(df.key.values, df.value.values)
    # fig, ax = plt.subplot()
    plt.xticks(rotation=45, ha='right', rotation_mode='anchor')
    plt.grid()
    plt.tight_layout()
    plt.show()

def plot_keyword(result, keyword=None):
    if keyword is None:
        keyword = list(result['keywords'].keys())[0]
    df = pd.DataFrame(result['keywords'][keyword]['match_ratio'])
    df[0].value_counts().plot(kind='pie')
    # plt.xticks(rotation=45, ha='right', rotation_mode='anchor')
    # plt.grid()
    plt.title(f'Composition of score of keyword "{keyword}"')
    plt.tight_layout()
    plt.show()


def get_counts(result):
    keys = result['keywords'].keys()
    df_counts = pd.DataFrame([(key, result['keywords'][key]['count']) for key in keys],
                             columns=['key', 'value'])
    return df_counts





if __name__ == '__main__':
    crawl_id = 4246
    if crawl_id is None:
        crawl_id = int(input('Enter crawl ID: '))
    ds = DataSourceSlim()
    analysis_result = ds.mongo.db.simpleanalysis.find_one({'crawl_id': 4243})
    df = get_counts(analysis_result)
    plot_counts(df)
    plot_keyword(result=analysis_result, keyword='umzug')
    pprint(analysis_result)