import asyncio
import logging
from dataclasses import dataclass
from typing import List
from subprocess import run

from multiprocessing import Pool
from digilog.DataSource import DataSourceContext, DataSource, QueueEntry

FORMAT = '%(asctime)s [QueueProcessor] %(levelname)s: %(message)s'
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
    run(['python', 'run_crawl.py', 'queued', str(entry.id), '-s', 'MAX_DEPTH=2'])


async def process_queue():
    while True:
        with DataSourceContext() as ds:
            options = get_run_options()
            queue_entries = get_queue_entries(ds, options.loading_chunk_size)
            if len(queue_entries) == 0:
                logger.info('No queue entries')
                await asyncio.sleep(options.delay_when_empty_seconds)
            else:
                with Pool(options.parallel_count) as p:
                    p.map(process_entry, queue_entries)


def get_run_options():
    return RunOptions(parallel_count=3, delay_when_empty_seconds=30, loading_chunk_size=6)


def get_queue_entries(ds: DataSource, max_entries: int) -> List[QueueEntry]:
    return ds.postgres.load_new_queue_entries(max_entries)


if __name__ == '__main__':
    asyncio.run(process_queue())
