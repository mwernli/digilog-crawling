import spacy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from spaczz.matcher import FuzzyMatcher
from urllib3.util import parse_url
from typing import List

import scrapy
from ..DataSource import DataSource
from ..items import RawItem


# from progressbar import progressbar



class PointerCrawlSpider(scrapy.Spider):
    # goes deeper in certain sub directions
    name = 'pointer'

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ds = DataSource()
        self.domain = '.'.join(parse_url(url).host.split('.')[-2:])
        self.logger.info('Initialized crawler "{}" on domain "{}"'.format(self.name, self.domain))
        self.link_extractor = LxmlLinkExtractor(allow_domains=[self.domain])
        self.url = url
        self.nlp = spacy.load('de_core_news_sm')
        self.matcher = FuzzyMatcher(self.nlp.vocab)
        self.keywords = ['mitarbeitende', 'online', 'dienstleistung']
        self.matcher.add('InterestingWord', [self.nlp(keyword) for keyword in self.keywords])

        self.crawl_id = self.ds.postgres.insert_crawl(url, self.name)
        self.logger.info("Inserted new crawl with ID: {}".format(self.crawl_id))
        
    def start_requests(self):
        yield scrapy.Request(self.url)

    def parse(self, response):
        html = response.text
        url = response.request.url
        depth = response.request.meta['depth']

        #print(f'---{url}---')
        # if response.meta['depth'] <= 2:
        if response.meta['depth'] <= 2:
            links = self.link_extractor.extract_links(response)
            yield RawItem(html=html, url=url, links=links, depth=depth)

            # for link in links:
            #     yield response.follow(link, self.parse)
        else:
            matches = self.matcher(self.nlp(' '.join(url.split('/'))))
            links = self.link_extractor.extract_links(response)
            if len(matches) > 0:
                yield RawItem(html=html, url=url, links=links, depth=depth)
            del matches

        for link in links:
            yield response.follow(link, self.parse)


    def closed(self, reason):
        self.logger.info('Closing spider with reason: "{}"'.format(reason))
        self.save_stats()
        self.ds.close()

    
    def save_stats(self):
        nested_stats = stats_to_nested_dict(self.crawler.stats.get_stats())
        stats_id = self.ds.mongodb.insert_crawl_stats(nested_stats, self.crawl_id, None)
        self.ds.postgres.insert_crawl_stats_connection(self.crawl_id, str(stats_id))


def stats_to_nested_dict(scrapy_stats: dict) -> dict:
    nested_stats = {}
    for composite_key, value in scrapy_stats.items():
        add_partial_key(nested_stats, value, composite_key.split('/'))
    return nested_stats


def add_partial_key(result_dict: dict, value, partial_keys: List[str]):
    if len(partial_keys) == 1:
        result_dict[partial_keys[0]] = value
    else:
        sub_dict = result_dict.setdefault(partial_keys[0], {})
        add_partial_key(sub_dict, value, partial_keys[1:])