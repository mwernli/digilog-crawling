import scrapy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from urllib3.util import parse_url

from ..DataSource import DataSource
from ..items import RawItem
from bs4 import BeautifulSoup

from spaczz.matcher import FuzzyMatcher
import spacy
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
        
    def start_requests(self):
        yield scrapy.Request(self.url)

    def parse(self, response):
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        raw_text = soup.get_text()
        url = response.request.url
        depth = response.request.meta['depth']

        #print(f'---{url}---')
        # if response.meta['depth'] <= 2:
        if response.meta['depth'] <= 2:
            links = self.link_extractor.extract_links(response)
            yield RawItem(html=html, raw_text=raw_text, url=url, links=links, depth=depth)

            # for link in links:
            #     yield response.follow(link, self.parse)
        else:
            matches = self.matcher(self.nlp(' '.join(url.split('/'))))
            links = self.link_extractor.extract_links(response)
            if len(matches) > 0:
                yield RawItem(html=html, raw_text=raw_text, url=url, links=links, depth=depth)
            del matches

        for link in links:
            yield response.follow(link, self.parse)



    def closed(self, reason):
        self.logger.info('Closing spider with reason: "{}"'.format(reason))
        self.ds.close()
