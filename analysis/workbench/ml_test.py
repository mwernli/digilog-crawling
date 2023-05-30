import pandas as pd
from bson.objectid import ObjectId
from DataSourceSlim import DataSourceSlim
from bs4 import BeautifulSoup
import re
import numpy as np
from progressbar import progressbar
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, StandardScaler, KernelCenterer, PowerTransformer
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
sns.set_style('darkgrid')
ds = DataSourceSlim()

class MLHittnau:
    def __init__(self):
        self.y_df, self.page_tf_idf = self.read_hittnau()
        self.get_htmls_to_results(self.y_df.index)

    def read_hittnau(self):
        df = pd.read_csv('../data/hittnau/df_tf_idf_hittnau.csv', index_col=0)
        df_tokens = pd.read_csv('../data/hittnau/df_hittnau_tokens.csv', index_col=0)
        self.df_hittnau = pd.concat([df, df_tokens[['tokens_uncleaned', 'token_values_uncleaned']]], axis=1)

        y = df.loc[df.y.notna(), 'y'].str.split(' ')
        split_data = {}
        keys = ['y_kind', 'y_classification', 'y_medium']
        for ind in y.index:
            split_data[ind] = {}
            for i in range(len(keys)):
                split_data[ind][keys[i]] = y.loc[ind][i]
        y_df = pd.DataFrame(split_data).transpose()
        X_df = df.drop('y', axis=1)
        return y_df, X_df

    def get_htmls_to_results(self, result_ids):
        id_url_list = [ds.postgres.interact_postgres(f'select url, mongo_id from crawl_result where id = {i}')[0] for i in result_ids]
        res_dict = {}
        for url, i in progressbar(id_url_list):
            res = ds.mongo.db.simpleresults.find_one({'_id': ObjectId(i)})
            res_dict[res['result_id']] = self.feature_engineering(res, url)
        self.df_feature = pd.DataFrame(res_dict).transpose()


    def feature_engineering(self, item, url) -> dict:
        internal_link_pattern = re.compile(r'^/.*|hittnau.ch')
        external_link_pattern = re.compile(r'^http')
        mail_link_pattern = re.compile(r'mailto:')
        pdf_link_pattern = re.compile(r'.pdf$')
        soup = BeautifulSoup(item['html'])
        hrefs = soup.find_all('a')
        n_hrefs_internal = np.sum([bool(re.search(internal_link_pattern, tag.get('href')))
                                   and not bool(re.search(external_link_pattern, tag.get('href')))
                                   and not bool(re.search(mail_link_pattern, tag.get('href')))
                                   for tag in hrefs if not tag.get('href') is None])
        n_hrefs_external = np.sum([not bool(re.search(internal_link_pattern, tag.get('href')))
                                   and bool(re.search(external_link_pattern, tag.get('href')))
                                   and not bool(re.search(mail_link_pattern, tag.get('href')))
                                   for tag in hrefs if not tag.get('href') is None])
        n_mail = np.sum([not bool(re.search(internal_link_pattern, tag.get('href')))
                                   and not bool(re.search(external_link_pattern, tag.get('href')))
                                   and bool(re.search(mail_link_pattern, tag.get('href')))
                                   for tag in hrefs if not tag.get('href') is None])

        if n_hrefs_external == 0:
            if n_hrefs_internal == 0:
                ratio_hrefs = 1
            else:
                ratio_hrefs = n_hrefs_internal
        else:
            ratio_hrefs = n_hrefs_internal/n_hrefs_external
            if ratio_hrefs < 1:
                ratio_hrefs = 1

        if n_mail == 0:
            if n_hrefs_internal == 0:
                ratio_mail = 1
            else:
                ratio_mail = n_hrefs_internal
        else:
            ratio_mail = n_hrefs_internal/n_mail
            if ratio_mail < 1:
                ratio_mail = 1

        n_inputs = len(soup.find_all('input'))

        text = re.sub(re.compile(r'\n+|\s+'), ' ', soup.get_text())
        l_text = len(text)
        if l_text >= 1:
            log_l_text = np.log(l_text)
        else:
            log_l_text = 0

        site_level = len([item for item in url.split('.')[-1].split('?')[0].split('/') if len(item)>0])
        # hotwords = get_hot_words()
        divs = soup.find_all('div')
        forms = soup.find_all('form')
        n_inputs_per_form = np.array([len(form.find_all('input')) for form in forms])
        # n_children_divs = [len([child for child in tag.children]) for tag in divs]
        #
        # if len(n_children_divs) == 0:
        #     divs_max_children = 0
        #     divs_mean_children = 0
        #     divs_median_children = 0
        # else:
        #     divs_max_children = np.max(n_children_divs)
        #     divs_mean_children = np.mean(n_children_divs)
        #     divs_median_children = np.median(n_children_divs)

        # n_h1 = len(soup.find_all('h1'))
        # n_h2 = len(soup.find_all('h2'))
        return {
            # 'crawl_id': item['crawl_id'],
            # 'result_id': item['result_id'],
            # 'n_inputs': np.sqrt(n_inputs),
            'n_inputs': n_inputs,
            'n_inputs_form_1': (n_inputs_per_form == 1).sum(),
            'n_inputs_form_2_3': ((n_inputs_per_form > 1) & (n_inputs_per_form < 4)).sum(),
            'n_inputs_form_4_': (n_inputs_per_form > 3).sum(),
            'l_text': log_l_text,
            # 'n_links': len(hrefs),
            'n_hrefs_internal': n_hrefs_internal,
            # 'n_hrefs_external': np.sqrt(n_hrefs_external),
            'n_hrefs_external': n_hrefs_external,
            # 'hrefs_ratios': np.log(ratio_hrefs),
            'hrefs_ratios': ratio_hrefs,
            # 'mail_ratio': np.log(ratio_mail),
            'mail_ratio': ratio_mail,
            # 'children_max': divs_max_children,
            # 'children_mean': divs_mean_children,
            # 'children_median': divs_median_children,
            # 'n_h1': n_h1,
            # 'n_h2': n_h2
            'site_level': site_level
        }

if __name__ == '__main__':
    # y, page_tf_idf = read_hittnau()
    # htmls = get_htmls_to_results(y.index)
    ml = MLHittnau()
    df = ml.df_feature
    df.loc[df.l_text > np.quantile(df.l_text, 0.98), 'l_text'] = np.quantile(df.l_text, 0.98)

    # scaler = MinMaxScaler()
    scaler = StandardScaler()
    # scaler = PowerTransformer()
    # scaler = KernelCenterer()
    df_scaled = pd.DataFrame(scaler.fit_transform(df), columns=df.columns, index=df.index)
    # df_scaled = df
    model = PCA(n_components=6)
    ar_decomp = model.fit_transform(df_scaled)
    df_decomp = pd.DataFrame(ar_decomp,
                             columns=['x'+str(1+i) for i in range(ar_decomp.shape[1])],
                             index=df_scaled.index)
    vars = pd.DataFrame([model.explained_variance_ratio_],
                      index=[0],
                      columns=list(range(len(model.explained_variance_ratio_))))
    g = sns.barplot(vars)
    g.set_xticks(range(len(model.explained_variance_ratio_)))
    g.set_xticklabels(np.cumsum(model.explained_variance_ratio_).round(2))
    plt.title('Covered variance ratio by dimension')
    plt.ylabel('Ratio (%/100')
    plt.xlabel('cummulative value of variance ratio covered')
    plt.savefig(f'../data/hittnau/plots/var_cover.jpeg')
    plt.show()

    print(np.cumsum(model.explained_variance_ratio_))
    # # g = sns.lineplot(np.cumsum(model.explained_variance_ratio_))
    # g.set_xticks(range(len(model.explained_variance_ratio_)))
    # g.set_xticklabels(np.cumsum(model.explained_variance_ratio_).round(2))
    # plt.show()
    # scaler = StandardScaler()
    # scaler = KernelCenterer()
    # scaler = PowerTransformer()
    # df_decomp_scaled = pd.DataFrame(scaler.fit_transform(df_decomp), columns=df_decomp.columns, index=df_decomp.index)
    df_decomp_scaled = pd.DataFrame(df_decomp, columns=df_decomp.columns, index=df_decomp.index)
    df_plot = pd.concat([ml.y_df, df_decomp], axis=1)
    df_plot = pd.concat([ml.y_df, df_decomp_scaled], axis=1)

    df_plot_simple = df_plot.copy()
    df_plot_simple.loc[(df_plot_simple.y_classification != 'bauen') & (df_plot_simple.y_classification != 'wohnen'), 'y_classification'] = 'sonstiges'
    # sns.scatterplot(data=df_plot_simple, x='x1', y='x2', hue='y_classification', alpha = 0.5)
    sns.scatterplot(data=df_plot, x='x1', y='x2', hue='y_classification', alpha = 0.5)
    plt.title('Page topic')
    plt.legend(fontsize='x-small')
    xlims = df_plot.x1.quantile(q=[0.01,0.99]).values
    ylims = df_plot.x2.quantile(q=[0.01,0.99]).values
    xlims = xlims + np.array([-1, 1]) * 0.1*np.abs(xlims[1]-xlims[0])
    ylims = ylims + np.array([-1, 1]) * 0.1*np.abs(ylims[1]-ylims[0])

    plt.ylim(ylims[0], ylims[1])
    plt.xlim(xlims[0], xlims[1])
    # plt.show()
    plt.savefig(f'../data/hittnau/plots/scatterplot_topic.jpeg')
    plt.show()
    counts = pd.DataFrame(dict(Counter(df_plot.y_classification)), index=['counts']).transpose()
    counts['classes'] = counts.index
    sns.barplot(counts, y='classes', x='counts')
    plt.title('Page topic')
    # plt.show()
    # plt.savefig(f'../data/hittnau/plots/barplot_topic.jpeg')
    plt.show()

    # sns.scatterplot(data=df_plot_simple, x='x1', y='x2', hue='y_medium', alpha = 0.5)
    sns.scatterplot(data=df_plot, x='x1', y='x2', hue='y_medium', alpha = 0.5)
    plt.title('How is the service delivered')
    plt.ylim(ylims[0], ylims[1])
    plt.xlim(xlims[0], xlims[1])
    # plt.show()
    # plt.savefig(f'../data/hittnau/plots/scatterplot_medium.jpeg')
    plt.show()
    counts = pd.DataFrame(dict(Counter(df_plot.y_medium)), index=['counts']).transpose()
    counts['classes'] = counts.index
    sns.barplot(counts, y='classes', x='counts')
    plt.title('How is the service delivered')
    # plt.show()
    plt.savefig(f'../data/hittnau/plots/barplot_medium.jpeg')
    plt.show()

    sns.scatterplot(data=df_plot, x='x1', y='x2', hue='y_kind', alpha = 0.5)
    plt.title('Kind of service')
    # plt.ylim(-2,4)
    # plt.xlim(-5,5)
    plt.ylim(ylims[0], ylims[1])
    plt.xlim(xlims[0], xlims[1])
    # plt.show()
    # plt.savefig(f'../data/hittnau/plots/scatterplot_servicekind.jpeg')
    plt.show()
    sns.barplot()
    counts = pd.DataFrame(dict(Counter(df_plot.y_kind)), index=['counts']).transpose()
    counts['classes'] = counts.index
    sns.barplot(counts, y='classes', x='counts')
    plt.title('Kind of service')
    # plt.show()
    plt.savefig(f'../data/hittnau/plots/barplot_servicekind.jpeg')
    plt.show()


    show_nlp = False
    if show_nlp:
        keyword_dict = {}
        for cat in list(set(df_plot.y_classification.values)):
            keyword_dict[cat] = {}
            index_class = df_plot.loc[df_plot.y_classification == cat].index
            tmp_df = ml.df_hittnau.loc[index_class]
            tmp_list = []
            for keywords in tmp_df.tokens:
                tmp_list.extend(keywords.split('  '))
            keyword_dict[cat]['list_cleaned'] = tmp_list
            keyword_dict[cat]['most_common_cleaned'] = Counter(tmp_list).most_common(10)
            tmp_list = []
            for keywords in tmp_df.tokens_uncleaned:
                tmp_list.extend(keywords.split('  '))
            keyword_dict[cat]['list_uncleaned'] = tmp_list
            keyword_dict[cat]['most_common_uncleaned'] = Counter(tmp_list).most_common(10)

        for key in keyword_dict.keys():
            tmp_df = pd.DataFrame(keyword_dict[key]['most_common_cleaned'],
                                  columns=[ 'keyword', 'counts'])
            tmp_df['counts'] = pd.to_numeric(tmp_df.counts)
            sns.barplot(tmp_df, x='counts', y='keyword')
            plt.yticks(fontsize='x-small', rotation=30)
            plt.title(f'{key} cleaned')
            # plt.show()
            plt.savefig(f'../data/hittnau/plots/keywords/{key}_cleaned.jpeg')
            plt.show()

            tmp_df = pd.DataFrame(keyword_dict[key]['most_common_uncleaned'],
                                  columns=[ 'keyword', 'counts'])
            tmp_df['counts'] = pd.to_numeric(tmp_df.counts)
            sns.barplot(tmp_df, x='counts', y='keyword')
            plt.yticks(fontsize='x-small', rotation=30)
            plt.title(f'{key} uncleaned')
            # plt.show()
            plt.savefig(f'../data/hittnau/plots/keywords/{key}_uncleaned.jpeg')
            plt.show()

