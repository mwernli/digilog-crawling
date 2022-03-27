from typing import List

from bs4 import BeautifulSoup
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from urllib3.util import parse_url

import scrapy
from ..DataSource import DataSource, QueueStatus
from ..items import RawItem
from ..pipelines import normalize_url


class QueuedEntrySpider(scrapy.Spider):
    name = 'queued'

    def __init__(self, queue_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ds = DataSource()
        self.queue_entry = self.ds.postgres.get_queue_entry_by_id(queue_id)
        self.ds.postgres.update_queue_status(queue_id, QueueStatus.IN_PROGRESS)
        parsed_url = parse_url(self.queue_entry.url)
        self.domain = '.'.join(parsed_url.host.split('.')[-2:])
        self.logger.info('Initialized queued crawler for id {} on domain "{}"'.format(self.queue_entry.id, self.domain))
        self.link_extractor = LxmlLinkExtractor(allow_domains=[self.domain])
        scheme = parsed_url.scheme or 'http://'
        normalized_url = scheme + normalize_url(self.queue_entry.url)

        self.crawl_id = self.ds.postgres.insert_crawl(normalized_url, self.name)
        self.logger.info("Inserted new crawl with URL {},  ID [{}]".format(normalized_url, self.crawl_id))

        self.url = normalized_url

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

        for link in filter(self.filter_extensions, links):
            yield response.follow(link, self.parse)

    def closed(self, reason):
        self.logger.info('Closing spider with reason: "{}"'.format(reason))
        status = QueueStatus.DONE if reason == 'finished' else QueueStatus.ERROR
        self.ds.postgres.update_queue_status(self.queue_entry.id, status, reason)
        self.save_stats()
        self.ds.close()

    def save_stats(self):
        nested_stats = stats_to_nested_dict(self.crawler.stats.get_stats())
        stats_id = self.ds.mongodb.insert_crawl_stats(nested_stats, self.crawl_id, self.queue_entry.id)
        self.ds.postgres.insert_crawl_stats_connection(self.crawl_id, str(stats_id))

    def filter_extensions(self, link):
        for extension in self.link_extractor.deny_extensions:
            if link.text.endswith(extension):
                self.logger.info(f'Filtering out link "{link}" because of extension "{extension}"')
                return False
        return True


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