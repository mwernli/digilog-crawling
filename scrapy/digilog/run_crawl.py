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
    subparsers = parser.add_subparsers(help='running modes')
    add_simple_spider_parser(subparsers)
    add_queued_parser(subparsers)
    arguments = parser.parse_args(args)
    return arguments


def add_simple_spider_parser(subparsers):
    simple_spider_parser = subparsers.add_parser('simple', help='the simple crawler spider')
    simple_spider_parser.set_defaults(func=run_simple)
    simple_spider_parser.add_argument('URL', type=str, help='The URL to start the crawl from')
    add_settings_parser(simple_spider_parser)
    return simple_spider_parser


def add_queued_parser(subparsers):
    queued_parser = subparsers.add_parser('queued', help='process a queue entry')
    queued_parser.set_defaults(func=run_queued)
    queued_parser.add_argument('id', type=int, help='The ID of the queue entry to process')
    add_settings_parser(queued_parser)
    return queued_parser


def add_settings_parser(parser):
    parser.add_argument('-s', type=str, nargs='*', dest='settings', metavar='KEY=VALUE', help='scrapy settings')


def run_simple(args):
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

    process.crawl('simple', url=args.URL)
    process.start()  # the script will block here until the crawling is finished


def run_queued(args):
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

    process.crawl('queued', queue_id=args.id)
    process.start()  # the script will block here until the crawling is finished


if __name__ == '__main__':
    parsed_args = parse_args(sys.argv[1:])
    parsed_args.func(parsed_args)
