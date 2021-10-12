# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RawItem(scrapy.Item):
    # define the fields for your item here like:
    html = scrapy.Field()
    raw_text = scrapy.Field()
    url = scrapy.Field()
    links = scrapy.Field()
