import argparse
import sys

import calibration
from logginghelpers import configure_logging

CALIBRATE_ALL_CMD = 'all'
CALIBRATE_MUNICIPALITY_CMD = 'municipality'


def parse_settings(settings) -> dict:
    result = {}
    if settings is not None:
        for setting in settings:
            k, v = setting.split('=')
            result[k] = v
    return result


def schedule_calibration_run(args):
    settings = parse_settings(args.override_settings)
    if args.calibrateSubCommand == CALIBRATE_ALL_CMD:
        calibration.schedule_for_all_municipalities(args.settings_key, settings, args.force_all, args.limit)
    elif args.calibrateSubCommand == CALIBRATE_MUNICIPALITY_CMD:
        calibration.schedule_for_single_municipality(args.municipality_id, args.settings_key, settings)


def add_settings_override_parser(parser):
    parser.add_argument('-o', '--override-settings', type=str, nargs='*', dest='override_settings', metavar='KEY=VALUE', help='override individual scrapy settings')


def add_settings_key_parser(parser, default):
    parser.add_argument('-s', '--settings-key', type=str, default=default, dest='settings_key', choices=['DEBUG_DEFAULT', 'DEBUG_CALIBRATE', 'CALIBRATE'], help='use settings stored in default_scrapy_settings with this key')


def add_calibration_parser(subparsers):
    schedule_calibration_parser = subparsers.add_parser('calibrate', help='schedule calibration runs')
    schedule_calibration_parser.set_defaults(func=schedule_calibration_run)

    calibration_subparsers = schedule_calibration_parser.add_subparsers(
        help='schedule calibration run for:', required=True, dest='calibrateSubCommand'
    )
    all_subparser = calibration_subparsers.add_parser(CALIBRATE_ALL_CMD,
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

    municipality_subparser = calibration_subparsers.add_parser(CALIBRATE_MUNICIPALITY_CMD,
                                                     help='given municipality id')
    municipality_subparser.add_argument('municipality_id', type=int, help='id of the municipality')
    add_settings_key_parser(municipality_subparser, 'CALIBRATE')
    add_settings_override_parser(municipality_subparser)


def parse_args(args):
    parser = argparse.ArgumentParser('scheduler.py')
    subparsers = parser.add_subparsers(help='scheduling types')
    add_calibration_parser(subparsers)
    arguments = parser.parse_args(args)
    return arguments


if __name__ == '__main__':
    configure_logging()
    parsed_args = parse_args(sys.argv[1:])
    if hasattr(parsed_args, 'func'):
        parsed_args.func(parsed_args)
    else:
        parse_args(['-h'])
