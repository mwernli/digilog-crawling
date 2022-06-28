import scrapy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor

from ..DataSource import DataSource, QueueStatus
from ..common import stats_to_nested_dict, get_domain_and_url
from ..items import RawItem


class QueuedEntrySpider(scrapy.Spider):
    name = 'queued'

    def __init__(self, queue_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ds = DataSource()
        self.queue_entry = self.ds.postgres.get_queue_entry_by_id(queue_id)
        self.ds.postgres.update_queue_status(queue_id, QueueStatus.IN_PROGRESS)
        self.domain, self.url = get_domain_and_url(self.queue_entry.url)
        self.logger.info(f'Initialized calibration crawler for id {self.queue_entry.id} on domain "{self.domain}"')
        self.link_extractor = LxmlLinkExtractor(allow_domains=[self.domain])
        self.allowed_domains = [self.domain]

        self.crawl_id = self.ds.postgres.insert_crawl(self.url, self.name)
        self.ds.postgres.insert_crawl_status(self.crawl_id, 'CRAWLING')
        self.logger.info(f'Inserted new crawl with URL {self.url}, ID [{self.crawl_id}]')

    def start_requests(self):
        yield scrapy.Request(self.url)

    def parse(self, response, **kwargs):
        html = response.text
        url = response.request.url
        depth = response.request.meta['depth']

        links = self.link_extractor.extract_links(response)

        yield RawItem(html=html, url=url, links=links, depth=depth)

        for link in filter(self.filter_extensions, links):
            yield response.follow(link, self.parse)

    def closed(self, reason):
        self.logger.info('Closing spider with reason: "{}"'.format(reason))
        status = QueueStatus.DONE if reason == 'finished' or reason == 'closespider_timeout' else QueueStatus.ERROR
        self.ds.postgres.update_queue_status(self.queue_entry.id, status, reason)
        self.ds.postgres.insert_crawl_status(self.crawl_id, 'CRAWLED')
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
