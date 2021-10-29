import sys
import argparse
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class NewlineRemovingFormatter(logging.Formatter):
    def __init__(self, log_format, log_date_format):
        super(NewlineRemovingFormatter, self).__init__(fmt=log_format, datefmt=log_date_format)

    def format(self, record: logging.LogRecord) -> str:
        default_log = super(NewlineRemovingFormatter, self).format(record)
        return default_log.replace('\n', '')


def parse_args(args):
    parser = argparse.ArgumentParser('Running a crawl')
    parser.add_argument('SpiderName', choices=['simple'], help='The name of the spider to use')
    parser.add_argument('URL', type=str, help='The URL to start the crawl from')
    parser.add_argument('-s', type=str, nargs='*', dest='settings', metavar='KEY=VALUE', help='scrapy settings')
    arguments = parser.parse_args(args)
    return arguments


def run_crawl(args):
    settings = get_project_settings()
    for setting in args.settings:
        key, value = setting.split('=')
        settings.set(key, value)
    log_level = settings.get('LOG_LEVEL')
    handler = logging.StreamHandler()
    handler.setFormatter(NewlineRemovingFormatter(settings.get('LOG_FORMAT'), settings.get('LOG_DATEFORMAT')))
    handler.setLevel(log_level)
    logging.basicConfig(handlers=[handler], level=settings.get('LOG_LEVEL'))

    process = CrawlerProcess(settings=settings, install_root_handler=False)

    process.crawl(args.SpiderName, url=args.URL)
    process.start()  # the script will block here until the crawling is finished


if __name__ == '__main__':
    parsed_args = parse_args(sys.argv[1:])
    run_crawl(parsed_args)
