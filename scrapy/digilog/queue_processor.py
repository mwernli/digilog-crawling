import logging
import os
from subprocess import run
from time import sleep

from digilog.DataSource import DataSourceContext, QueueEntry

FORMAT = '%(asctime)s [QueueProcessor] [main] %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
logging_target = 'STDOUT'
try:
    logging_target = os.environ['QUEUE_PROCESSOR_LOGGING_TARGET']
except KeyError:
    pass
if logging_target != 'STDOUT':
    logging.basicConfig(
        format=FORMAT,
        datefmt=DATE_FORMAT,
        filename=logging_target,
        filemode='a',
    )
else:
    logging.basicConfig(
        format=FORMAT,
        datefmt=DATE_FORMAT,
    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_entry(entry: QueueEntry):
    settings = [f'{k}={v}' for k, v in entry.settings.items()]
    if len(settings) > 0:
        settings = ['-s'] + settings
    run(['python', 'run_crawl.py', entry.crawl_type, str(entry.id)] + settings)


def process_queue():
    counter = 0
    while True:
        with DataSourceContext() as ds:
            queue_entry = ds.postgres.load_next_queue_entry()
            if queue_entry is None:
                if counter == 0:
                    logger.info('No queue entries')
                sleep(5)
                counter = (counter + 1) % 12
            else:
                process_entry(queue_entry)


if __name__ == '__main__':
    process_queue()
