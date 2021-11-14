from typing import Iterator

from .model import CrawlEntity
from ..common.model import DataSource


def load_crawls(ds: DataSource) -> Iterator[CrawlEntity]:
    with ds.postgres_cursor() as c:
        c.execute("""
        SELECT * FROM digilog.digilog.crawl;
        """)
        return map(CrawlEntity.from_record, c.fetchall())
