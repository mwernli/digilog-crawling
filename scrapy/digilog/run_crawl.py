import argparse
import logging
import os
import os.path
import sys

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
    add_calibration_parser(subparsers)
    add_pointer_parser(subparsers)
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


def add_calibration_parser(subparsers):
    queued_parser = subparsers.add_parser('calibration', help='perform a calibration run')
    queued_parser.set_defaults(func=run_calibration)
    queued_parser.add_argument('id', type=int, help='The ID of the queue entry to process')
    add_settings_parser(queued_parser)
    return queued_parser


def add_pointer_parser(subparsers):
    pointer_spider_parser = subparsers.add_parser('pointer', help='the pointer crawler spider')
    pointer_spider_parser.set_defaults(func=run_pointer)
    pointer_spider_parser.add_argument('URL', type=str, help='The URL to start the crawl from')
    add_settings_parser(pointer_spider_parser)
    return pointer_spider_parser    


def add_settings_parser(parser):
    parser.add_argument('-s', type=str, nargs='*', dest='settings', metavar='KEY=VALUE', help='scrapy settings')


def merge_settings_with_args(settings_args):
    settings = get_project_settings()
    for setting in settings_args:
        key, value = setting.split('=')
        settings.set(key, value)
    return settings


def get_logging_target():
    try:
        return os.environ['CRAWL_LOGGING_TARGET']
    except KeyError:
        return 'STDOUT'


def get_handler():
    try:
        target = get_logging_target()
        if target == 'STDOUT':
            return logging.StreamHandler()
        return logging.FileHandler(filename=target, mode='a')
    except FileNotFoundError:
        os.makedirs('/tmp/log/scrapy/', mode=0o777)
        return logging.FileHandler(filename='/tmp/log/scrapy/crawl.log', mode='a')


def configure_logging(settings, log_format=None):
    if log_format is None:
        log_format = settings.get('LOG_FORMAT')
    log_level = settings.get('LOG_LEVEL')
    handler = get_handler()
    handler.setFormatter(NewlineRemovingFormatter(log_format, settings.get('LOG_DATEFORMAT')))
    handler.setLevel(log_level)
    logging.basicConfig(handlers=[handler], level=settings.get('LOG_LEVEL'))


def run_simple(args):
    settings = merge_settings_with_args(args.settings)

    configure_logging(settings)

    process = CrawlerProcess(settings=settings, install_root_handler=False)

    process.crawl('simple', url=args.URL)
    process.start()  # the script will block here until the crawling is finished


def run_queued(args):
    settings = merge_settings_with_args(args.settings)

    configured_log_format = str(settings.get('LOG_FORMAT'))
    queued_log_format = configured_log_format.replace('%(asctime)s', '%(asctime)s [queue-entry-{}]'.format(args.id))
    configure_logging(settings, queued_log_format)

    process = CrawlerProcess(settings=settings, install_root_handler=False)

    process.crawl('queued', queue_id=args.id)
    process.start()  # the script will block here until the crawling is finished


def run_calibration(args):
    settings = merge_settings_with_args(args.settings)

    configured_log_format = str(settings.get('LOG_FORMAT'))
    queued_log_format = configured_log_format.replace(
        '%(asctime)s', '%(asctime)s [calibration-queue-entry-{}]'.format(args.id)
    )
    configure_logging(settings, queued_log_format)

    process = CrawlerProcess(settings=settings, install_root_handler=False)

    process.crawl('calibration', queue_id=args.id)
    process.start()


def run_pointer(args):
    settings = merge_settings_with_args(args.settings)

    configure_logging(settings)

    process = CrawlerProcess(settings=settings, install_root_handler=False)

    process.crawl('pointer', url=args.URL)
    process.start()  # the script will block here until the crawling is finished


if __name__ == '__main__':
    parsed_args = parse_args(sys.argv[1:])
    parsed_args.func(parsed_args)
