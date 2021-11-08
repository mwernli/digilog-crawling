import asyncio
import logging
from dataclasses import dataclass
from typing import List
from subprocess import run

from multiprocessing import Pool
from digilog.DataSource import DataSourceContext, DataSource, QueueEntry

FORMAT = '%(asctime)s [QueueProcessor] %(levelname)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass(frozen=True)
class RunOptions:
    parallel_count: int
    delay_when_empty_seconds: int


def process_entry(entry: QueueEntry):
    run(['python', 'run_crawl.py', 'queued', str(entry.id), '-s', 'MAX_DEPTH=2'])


async def process_queue():
    while True:
        with DataSourceContext() as ds:
            options = get_run_options()
            queue_entries = get_queue_entries(ds)
            if len(queue_entries) == 0:
                logger.info('No queue entries')  # TODO better format for log output
                await asyncio.sleep(options.delay_when_empty_seconds)
            else:
                with Pool(options.parallel_count) as p:
                    p.map(process_entry, queue_entries)


# TODO add run options table in database and load from there
def get_run_options():
    return RunOptions(3, 30)


# TODO logging?
def get_queue_entries(ds: DataSource) -> List[QueueEntry]:
    return ds.postgres.load_new_queue_entries()


if __name__ == '__main__':
    asyncio.run(process_queue())
