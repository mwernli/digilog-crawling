from DataSourceSlim import DataSourceSlim
from collections import Counter
from bs4 import BeautifulSoup

class SocialMediaAnalysis:
    def __init__(self, **kwargs):
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None
        self.social_media_score = None
        self.instagram_names = []
        self.facebook_names = []
        self.youtube_names = []
        self.twitter_names = []
        self.links = None
        self.hrefs = None
        self.link_names = None
        self.ds = DataSourceSlim()
        self.social_media_dict = social_media_dict = {
            'facebook': {
                'account': None,
                'names': [],
                'counts': [],
                'all_urls': []
            },
            'instagram': {
                'account': None,
                'names': [],
                'counts': [],
                'all_urls': []
            },
            'twitter': {
                'account': None,
                'names': [],
                'counts': [],
                'all_urls': []
            },
            'youtube': {
                'account': None,
                'names': [],
                'counts': [],
                'all_urls': []
            },
        }
        # self.analyze()

    def __repr__(self):
        return "crawl_id: %s\ntop_url: %s\nscore: %s/%s\nFacebook account: %s\nTwitter account: %s\nInstagram account: %s\nYoutube account: %s\n" % \
               (self.crawl_id,
                self.ds.postgres.interact_postgres(
                    f'SELECT top_url FROM crawl WHERE id = {self.crawl_id}'),
                self.social_media_score,
                len(list(self.social_media_dict.keys())),
                self.social_media_dict['facebook']['account'],
                self.social_media_dict['twitter']['account'],
                self.social_media_dict['instagram']['account'],
                self.social_media_dict['youtube']['account']
                )

    def analyze(self):
        if self.hrefs is None:
            self.get_crawl_results()
        self.run_social_media_analysis()

    def get_crawl_results(self):
        if self.crawl_id is None:
            raise 'If not provided at __ini__ crawl_id must be provided before calling method get_crawl_result()'
        if self.crawlresults is None:
            self.crawlresults = [item for item in self.ds.mongo.db.simpleresults.find({'crawl_id': self.crawl_id})]
        self.links = [(tag.get_text(), tag.get('href')) for page in self.crawlresults for tag in
                      BeautifulSoup(page['html'], features='html.parser').find_all('a')]
        self.hrefs = [href for text, href in self.links]
        self.link_names = [text for text, href in self.links]

    def run_social_media_analysis(self):
        self.social_media_score = 0
        for href in self.hrefs:
            if not href is None:
                if 'facebook.com/' in href:
                    self.social_media_dict['facebook']['all_urls'].append(href)
                    self.facebook_case(href)
                if 'instagram.com/' in href:
                    self.social_media_dict['instagram']['all_urls'].append(href)
                    self.instragram_case(href)
                if 'youtube.com/' in href:
                    self.social_media_dict['youtube']['all_urls'].append(href)
                    self.youtube_case(href)
                if 'twitter.com/' in href:
                    self.social_media_dict['twitter']['all_urls'].append(href)
                    self.twitter_case(href)

        self.social_media_dict['twitter']['names'], self.social_media_dict['twitter'][
            'counts'] = self.get_sorted_counts(self.twitter_names)
        if len(self.social_media_dict['twitter']['names']) > 0:
            self.social_media_dict['twitter']['account'] = self.social_media_dict['twitter']['names'][0]
            self.social_media_score += 1

        self.social_media_dict['instagram']['names'], self.social_media_dict['instagram'][
            'counts'] = self.get_sorted_counts(self.instagram_names)
        if len(self.social_media_dict['instagram']['names']) > 0:
            self.social_media_dict['instagram']['account'] = self.social_media_dict['instagram']['names'][0]
            self.social_media_score += 1

        self.social_media_dict['youtube']['names'], self.social_media_dict['youtube'][
            'counts'] = self.get_sorted_counts(self.youtube_names)
        if len(self.social_media_dict['youtube']['names']) > 0:
            self.social_media_dict['youtube']['account'] = self.social_media_dict['youtube']['names'][0]
            self.social_media_score += 1

        self.social_media_dict['facebook']['names'], self.social_media_dict['facebook'][
            'counts'] = self.get_sorted_counts(self.facebook_names)
        if len(self.social_media_dict['facebook']['names']) > 0:
            self.social_media_dict['facebook']['account'] = self.social_media_dict['facebook']['names'][0]
            self.social_media_score += 1

        self.social_media_score = self.social_media_score/len(list(self.social_media_dict.keys()))


    def calculate_score(self):
        score = 0
        for key in list(self.social_media_dict.keys()):
            score += int(len(self.social_media_dict[key]['names']) > 0)
        self.social_media_dict['score'] = score
        return self.social_media_dict

    def twitter_case(self, href):
        cleaned_href = href.split('?')[0].replace('https://twitter.com/', '')
        # for item in cleaned_url:
        twitter_path = [part for part in cleaned_href.split('/') if len(part) > 0]
        if not len(twitter_path) > 1:
            self.twitter_names.append('@'+twitter_path[0])

    def instragram_case(self, href):
        cleaned_href = href.split('?')[0].replace('https://www.instagram.com/', '')
        # for item in cleaned_url:
        insta_path = [part for part in cleaned_href.split('/') if len(part) > 0]
        if not len(insta_path) > 1:
            self.instagram_names.append('@'+insta_path[0])

    def facebook_case(self, href):
        cleaned_href = href.split('?')[0].split('facebook.com/')[1]

        # for item in cleaned_url:
        facebook_path = [part for part in cleaned_href.split('/') if len(part) > 0]
        if not len(facebook_path) > 1:
            self.facebook_names.append(facebook_path[0])

    def youtube_case(self, href):
        cleaned_href = href.split('?')[0].split('youtube.com/')[1]
        # for item in cleaned_url:
        youtube_path = [part for part in cleaned_href.split('/') if len(part) > 0]
        if youtube_path[0] == 'user':
            self.youtube_names.append(youtube_path[1])

    def get_sorted_counts(self, nameslist: list) -> tuple:
        if len(nameslist) == 0:
            return [], []
        countdict = dict(Counter(nameslist))
        keys = list(countdict.keys())
        values = list(countdict.values())
        # sorted_index = sorted(range(len(values)), reverse=True, key=lambda k: values[k])
        sorted_values = sorted(values, reverse=True)
        sorted_keys = sorted(keys, reverse=True, key=lambda k: countdict[k])
        return sorted_keys, sorted_values

class SocialMediaAnalysisContext:
    def __init__(self, **kwargs):
        if 'crawl_id' in list(kwargs.keys()):
            self.crawl_id = kwargs['crawl_id']
        else:
            self.crawl_id = None
        if 'crawlresults' in list(kwargs.keys()):
            self.crawlresults = kwargs['crawlresults']
        else:
            self.crawlresults = None

    def __enter__(self) -> SocialMediaAnalysis:
        self._sma = SocialMediaAnalysis(crawl_id=self.crawl_id, crawlresults=self.crawlresults)
        return self._sma

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self._sma

if __name__ == '__main__':
    pass
    # obj = SocialMediaAnalysis(2035) #Genf
    # Dardagny = SocialMediaAnalysis(crawl_id=2034)  # Dardagny
    # Dardagny.analyze()
    # obj = SocialMediaAnalysis(817) #Lostorf
    # Uster = SocialMediaAnalysis(crawl_id=163)  # Uster
    # Uster.analyze()