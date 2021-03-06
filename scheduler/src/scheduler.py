import argparse
import sys

import analyse
import calibration
import crawl
from logginghelpers import configure_logging

ALL_CMD = 'all'
MUNICIPALITY_CMD = 'municipality'
FILE_CMD = 'file'
LATEST_CMD = 'latest'


def parse_settings(settings) -> dict:
    result = {}
    if settings is not None:
        for setting in settings:
            k, v = setting.split('=')
            result[k] = v
    return result


def schedule_calibration_run(args):
    settings = parse_settings(args.override_settings)
    tags = args.tags
    if tags is None:
        tags = []
    if args.calibrateSubCommand == ALL_CMD:
        calibration.schedule_for_all_municipalities(args.settings_key, settings, args.force_all, args.limit, tags)
    elif args.calibrateSubCommand == MUNICIPALITY_CMD:
        calibration.schedule_for_single_municipality(args.municipality_id, args.settings_key, settings, tags)


def analyse_data(args):
    tags = args.tags if hasattr(args, 'tags') else None
    if tags is None:
        tags = []
    if args.analyseSubCommand == FILE_CMD:
        analyse.analyse_all_calibration_runs_to_file(args.output_file, args.limit, tags)
    elif args.analyseSubCommand == LATEST_CMD:
        analyse.analyse_latest(args.limit)


def analyse_manuals(args):
    analyse.analyse_runs_with_manual_check(args.limit)


def analyse_urls(args):
    analyse.check_urls(args.limit, args.not_checked_since_days, args.max_attempts)


def schedule_crawls(args):
    tags = args.tags or []
    crawl.schedule_crawling_runs(args.limit, args.crawlType, args.days_since_last_success, tags)


def add_settings_override_parser(parser):
    parser.add_argument('-o', '--override-settings', type=str, nargs='*', dest='override_settings', metavar='KEY=VALUE', help='override individual scrapy settings')


def add_tags_parser(parser, help_text):
    parser.add_argument('-t', '--tags', type=str, nargs='*', dest='tags', metavar='TAG_VALUE', help=help_text)


def add_settings_key_parser(parser, default):
    parser.add_argument('-s', '--settings-key', type=str, default=default, dest='settings_key', help='use settings stored in default_scrapy_settings with this key')


def add_calibration_parser(subparsers):
    schedule_calibration_parser = subparsers.add_parser('calibrate', help='schedule calibration runs')
    schedule_calibration_parser.set_defaults(func=schedule_calibration_run)

    calibration_subparsers = schedule_calibration_parser.add_subparsers(
        help='schedule calibration run for:', required=True, dest='calibrateSubCommand'
    )
    all_subparser = calibration_subparsers.add_parser(ALL_CMD,
                                                      help='all municipalities')
    all_subparser.add_argument(
        '-f',
        '--force',
        default=False,
        action='store_true',
        dest='force_all',
        help='Schedule calibration run for all municipalities even if they are already calibrated',
    )
    all_subparser.add_argument(
        '-l',
        '--limit',
        type=int,
        dest='limit',
        help='limit amount of runs to be scheduled',
    )
    add_settings_key_parser(all_subparser, 'CALIBRATE')
    add_settings_override_parser(all_subparser)
    add_tags_parser(all_subparser, 'tags to attach to the created queue entries')

    municipality_subparser = calibration_subparsers.add_parser(MUNICIPALITY_CMD,
                                                               help='given municipality id')
    municipality_subparser.add_argument('municipality_id', type=int, help='id of the municipality')
    add_settings_key_parser(municipality_subparser, 'CALIBRATE')
    add_settings_override_parser(municipality_subparser)
    add_tags_parser(municipality_subparser, 'tags to attach to the created queue entry')


def add_analyse_parser(subparsers):
    analyse_parser = subparsers.add_parser('analyse', help='analyse data')
    analyse_subparsers = analyse_parser.add_subparsers(help='analyse what')
    parser = analyse_subparsers.add_parser('calibration', help='analyse calibration runs')
    parser.set_defaults(func=analyse_data)
    calibration_subparser = parser.add_subparsers(required=True, dest='analyseSubCommand', help='analyse calibration runs')
    all_subparser = calibration_subparser.add_parser(FILE_CMD, help='analyse all finished calibration runs and save as file')
    all_subparser.add_argument('-o', '--output-file', type=str, help='output data to this csv file', required=True)
    all_subparser.add_argument(
        '-l',
        '--limit',
        type=int,
        dest='limit',
        help='limit amount of runs to be analysed',
    )
    add_tags_parser(all_subparser, 'only entries which contain all of the specified tags')

    latest_subparser = calibration_subparser.add_parser(LATEST_CMD, help='analyse latest finished runs of uncalibrated municipalities')
    latest_subparser.add_argument(
        '-l',
        '--limit',
        type=int,
        dest='limit',
        help='limit amount of runs to be analysed',
    )

    manuals_subparser = analyse_subparsers.add_parser('manual-check', help='analyse urls with manual check flag')
    manuals_subparser.set_defaults(func=analyse_manuals)
    manuals_subparser.add_argument(
        '-l',
        '--limit',
        type=int,
        dest='limit',
        help='limit amount of entries to be analysed',
    )

    url_check_subparser = analyse_subparsers.add_parser('urls', help='check urls for validity or redirects')
    url_check_subparser.set_defaults(func=analyse_urls)
    url_check_subparser.add_argument(
        '-s',
        '--not-checked-since-days',
        type=int,
        required=True,
        help='minimum amount of days since last check',
    )
    url_check_subparser.add_argument(
        '-m',
        '--max-attempts',
        type=int,
        required=True,
        help='maximum amount of attempts before marking municipality as uncrawlable',
    )
    url_check_subparser.add_argument(
        '-l',
        '--limit',
        type=int,
        dest='limit',
        help='limit amount of entries to be analysed',
    )


def add_crawl_scheduling_parser(subparsers):
    crawl_parser = subparsers.add_parser('crawl', help='schedule municipality crawls')
    crawl_parser.set_defaults(func=schedule_crawls)
    # must match spider's name attribute
    crawl_parser.add_argument('crawlType', help='name of spider', choices=['pointer', 'queued', 'simple'])
    crawl_parser.add_argument('-d', '--days-since-last-success', type=int, required=True,
                              help='Days since last successful crawl of that crawl type')
    add_tags_parser(crawl_parser, 'additional tags for the queue entry')
    crawl_parser.add_argument(
        '-l',
        '--limit',
        type=int,
        dest='limit',
        help='limit amount of entries to be analysed',
    )


def parse_args(args):
    parser = argparse.ArgumentParser('scheduler.py')
    subparsers = parser.add_subparsers(help='action types')
    add_calibration_parser(subparsers)
    add_analyse_parser(subparsers)
    add_crawl_scheduling_parser(subparsers)
    arguments = parser.parse_args(args)
    return arguments


if __name__ == '__main__':
    configure_logging()
    parsed_args = parse_args(sys.argv[1:])
    if hasattr(parsed_args, 'func'):
        parsed_args.func(parsed_args)
    else:
        parse_args(['-h'])
