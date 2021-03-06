import logging
import os
from logging import Formatter

from datasource import get_env_str_or


def get_logging_target():
    try:
        return os.environ['SCHEDULER_LOGGING_TARGET']
    except KeyError:
        return 'STDOUT'


def get_pod_name():
    try:
        return os.environ['POD_NAME']
    except KeyError:
        return 'LOCAL'


def get_loki_handler():
    from logging_loki import LokiHandler, emitter

    emitter.LokiEmitter.level_tag = 'level'

    loki_host = get_env_str_or('LOKI_SERVICE_HOST', 'localhost')
    loki_port = get_env_str_or('LOKI_SERVICE_PORT', '3100')
    return LokiHandler(
        url=f'http://{loki_host}:{loki_port}/loki/api/v1/push',
        tags={'component': 'scheduler', 'pod': get_pod_name()},
        version='1',
    )


def get_handler():
    try:
        target = get_logging_target()
        if target == 'STDOUT':
            return logging.StreamHandler()
        elif target == 'LOKI':
            return get_loki_handler()
        else:
            return logging.FileHandler(filename=target, mode='a')
    except FileNotFoundError:
        return logging.StreamHandler()


def configure_logging():
    log_level = 'INFO'
    handler = get_handler()
    handler.setLevel(log_level)
    fmt = Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
    handler.setFormatter(fmt)
    logging.basicConfig(handlers=[handler], level=log_level)
