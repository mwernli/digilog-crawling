from typing import Iterator

from ..common.model import DataSource
from ..repository.crawlrepository import load_crawls
from ..repository.model import CrawlEntity


def load_all_crawls(ds: DataSource) -> Iterator[CrawlEntity]:
    return load_crawls(ds)
