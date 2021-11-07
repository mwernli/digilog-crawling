import scrapy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from urllib3.util import parse_url

from ..DataSource import DataSource, QueueStatus
from ..items import RawItem
from bs4 import BeautifulSoup


class QueuedEntrySpider(scrapy.Spider):
    name = 'queued'

    def __init__(self, queue_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ds = DataSource()
        self.queue_entry = self.ds.postgres.get_queue_entry_by_id(queue_id)
        self.ds.postgres.update_queue_status(queue_id, QueueStatus.IN_PROGRESS)
        self.domain = '.'.join(parse_url(self.queue_entry.url).host.split('.')[-2:])
        self.logger.info('Initialized queued crawler for id {} on domain "{}"'.format(self.queue_entry.id, self.domain))
        self.link_extractor = LxmlLinkExtractor(allow_domains=[self.domain])
        self.url = self.queue_entry.url

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

    def closed(self, reason):
        self.logger.info('Closing spider with reason: "{}"'.format(reason))
        status = QueueStatus.DONE if reason == 'finished' else QueueStatus.ERROR
        self.ds.postgres.update_queue_status(self.queue_entry.id, status, reason)
        self.ds.close()
