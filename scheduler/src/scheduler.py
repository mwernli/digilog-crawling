import argparse
import sys

import analyse
import calibration
from logginghelpers import configure_logging

ALL_CMD = 'all'
MUNICIPALITY_CMD = 'municipality'


def parse_settings(settings) -> dict:
    result = {}
    if settings is not None:
        for setting in settings:
            k, v = setting.split('=')
            result[k] = v
    return result


def schedule_calibration_run(args):
    settings = parse_settings(args.override_settings)
    if args.calibrateSubCommand == ALL_CMD:
        calibration.schedule_for_all_municipalities(args.settings_key, settings, args.force_all, args.limit, tags)
    elif args.calibrateSubCommand == MUNICIPALITY_CMD:
        calibration.schedule_for_single_municipality(args.municipality_id, args.settings_key, settings, tags)


def analyse_data(args):
    tags = args.tags
    if tags is None:
        tags = []
    if args.analyseSubCommand == ALL_CMD:
        analyse.analyse_all_calibration_runs(args.output_file, args.limit, tags)


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
    all_subparser = calibration_subparser.add_parser(ALL_CMD, help='analyse all finished calibration runs')
    all_subparser.add_argument('-o', '--output-file', type=str, help='output data to this csv file', required=True)
    all_subparser.add_argument(
        '-l',
        '--limit',
        type=int,
        dest='limit',
        help='limit amount of runs to be analysed',
    )
    add_tags_parser(all_subparser, 'only entries which contain all of the specified tags')


def parse_args(args):
    parser = argparse.ArgumentParser('scheduler.py')
    subparsers = parser.add_subparsers(help='action types')
    add_calibration_parser(subparsers)
    add_analyse_parser(subparsers)
    arguments = parser.parse_args(args)
    return arguments


if __name__ == '__main__':
    configure_logging()
    parsed_args = parse_args(sys.argv[1:])
    if hasattr(parsed_args, 'func'):
        parsed_args.func(parsed_args)
    else:
        parse_args(['-h'])
