import logging
import os
from logging import Formatter


def get_logging_target():
    try:
        return os.environ['SCHEDULER_LOGGING_TARGET']
    except KeyError:
        return 'STDOUT'


def get_handler():
    try:
        target = get_logging_target()
        if target != 'STDOUT':
            return logging.FileHandler(filename=target, mode='a')
        else:
            return logging.StreamHandler()
    except FileNotFoundError:
        return logging.StreamHandler()


def configure_logging():
    log_level = 'INFO'
    handler = get_handler()
    handler.setLevel(log_level)
    fmt = Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
    handler.setFormatter(fmt)
    logging.basicConfig(handlers=[handler], level=log_level)
