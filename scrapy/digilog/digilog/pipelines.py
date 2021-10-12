# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import re
from .DataSource import DataSource
from urllib3.util import parse_url
from w3lib.url import canonicalize_url


def normalize_url(s: str) -> str:
    url = parse_url(s)
    without_protocol = ''.join([
        url.host,
        re.sub(r'/\Z', '', url.path),
        '' if url.query is None else '?{}'.format(url.query)
    ])
    return canonicalize_url(without_protocol)


class SimplePipeline:
    def __init__(self):
        self.ds = None
        self.crawl_id = None
        self.url_dict = {}

    def open_spider(self, spider):
        self.ds = DataSource()
        url = normalize_url(spider.url)
        self.crawl_id = self.ds.postgres.insert_crawl(url)
        print("inserted new crawl with ID: {}".format(self.crawl_id))
        head_id = self.ds.postgres.insert_first_result_record(self.crawl_id, url)
        self.url_dict[url] = head_id

    def process_item(self, item, spider):
        url = normalize_url(item['url'])
        links = item['links']
        if url in self.url_dict:
            parent_id = self.url_dict[url]
        else:
            print("WARNING: parent URL not found: {} in {}".format(url, self.url_dict))
            parent_id = None
        mongo_id = self.ds.mongodb.insert_crawl_result(self.crawl_id, parent_id, item['html'], item['raw_text'])
        self.ds.postgres.update_mongo_id(parent_id, str(mongo_id))
        children = self.ds.postgres.insert_child_links(self.crawl_id, parent_id, links, normalize_url)
        self.url_dict.update(children)

    def close_spider(self, spider):
        print("closing")
        self.ds.close()
