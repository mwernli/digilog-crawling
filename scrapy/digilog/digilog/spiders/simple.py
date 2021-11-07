import scrapy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from urllib3.util import parse_url

from ..DataSource import DataSource
from ..items import RawItem
from bs4 import BeautifulSoup


class SimpleSpider(scrapy.Spider):
    name = 'simple'

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ds = DataSource()
        self.domain = '.'.join(parse_url(url).host.split('.')[-2:])
        self.logger.info('Initialized crawler "{}" on domain "{}"'.format(self.name, self.domain))
        self.link_extractor = LxmlLinkExtractor(allow_domains=[self.domain])
        self.url = url

    def start_requests(self):
        yield scrapy.Request(self.url)

    def parse(self, response):
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        raw_text = soup.get_text()
        url = response.request.url
        depth = response.request.meta['depth']

        links = self.link_extractor.extract_links(response)

        yield RawItem(html=html, raw_text=raw_text, url=url, links=links, depth=depth)

        for link in links:
            yield response.follow(link, self.parse)
