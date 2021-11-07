import asyncio
import logging
from dataclasses import dataclass
from typing import List
from subprocess import run

from multiprocessing import Pool

from digilog.DataSource import DataSourceContext


@dataclass(frozen=True)
class RunOptions:
    parallel_count: int
    delay_when_empty_seconds: int


@dataclass(frozen=True)
class QueueEntry:
    crawler: str
    url: str


def process_entry(entry: QueueEntry):
    run(["python", "run_crawl.py", entry.crawler, entry.url, "-s", "MAX_DEPTH=1"])


async def process_queue():
    logger = logging.getLogger(__name__)
    with DataSourceContext() as ds:
        options = get_run_options()
        while True:
            queue_entries = get_queue_entries()
            if len(queue_entries) == 0:
                logger.info('No queue entries')  # TODO better format for log output
                await asyncio.sleep(options.delay_when_empty_seconds)
            else:
                with Pool(options.parallel_count) as p:
                    p.map(process_entry, queue_entries)


# TODO add run options table in database and load from there
def get_run_options():
    return RunOptions(3, 30)


# TODO add queue table in database and load from there
entries = [QueueEntry('simple', 'https://quotes.toscrape.com')]


def get_queue_entries() -> List[QueueEntry]:
    if len(entries) > 0:
        return [entries.pop()]
    else:
        return []


if __name__ == '__main__':
    asyncio.run(process_queue())
