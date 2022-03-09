# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import logging
import re

from urllib3.util import parse_url
from w3lib.url import canonicalize_url

logger = logging.getLogger(__name__)


def normalize_url(s: str) -> str:
    try:
        url = parse_url(s)
        path = '' if url.path is None else re.sub(r'/\Z', '', url.path)
        query = '' if url.query is None else '?{}'.format(url.query)
        without_protocol = ''.join([
            url.host,
            re.sub(r'/\Z', '', path),
            query
        ])
        return canonicalize_url(without_protocol)
    except Exception as e:
        logger.exception('Unable to normalize input URL {}'.format(s))
        return s


class SimplePipeline:
    def __init__(self):
        self.url_dict = {}

    def open_spider(self, spider):
        url = normalize_url(spider.url)
        if not hasattr(spider, 'crawl_id'):
            spider.crawl_id = spider.ds.postgres.insert_crawl(url)
            logger.info("Inserted new crawl with ID: {}".format(spider.crawl_id))
        head_id = spider.ds.postgres.insert_result_record(spider.crawl_id, url)
        self.url_dict[url] = head_id
        if hasattr(spider, 'queue_entry'):
            spider.ds.postgres.insert_queue_crawl_connection(spider.queue_entry.id, spider.crawl_id)

    def process_item(self, item, spider):
        url = normalize_url(item['url'])
        current_id = spider.ds.postgres.insert_result_record(spider.crawl_id, url)
        mongo_id = spider.ds.mongodb.insert_crawl_result(spider.crawl_id, current_id, item['html'], item['raw_text'])
        spider.ds.postgres.update_mongo_id(current_id, str(mongo_id))
        spider.ds.postgres.insert_child_links(spider.crawl_id, item['links'], normalize_url)
