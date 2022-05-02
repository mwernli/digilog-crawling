import logging
from dataclasses import dataclass
from subprocess import run
from time import sleep

from digilog.DataSource import DataSourceContext, QueueEntry

FORMAT = '%(asctime)s [QueueProcessor] [main] %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=FORMAT, datefmt=DATE_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass(frozen=True)
class RunOptions:
    parallel_count: int
    delay_when_empty_seconds: int
    loading_chunk_size: int


def process_entry(entry: QueueEntry):
    run(['python', 'run_crawl.py', 'queued', str(entry.id), '-s', 'DEPTH_LIMIT=2'])


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
