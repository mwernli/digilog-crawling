from typing import Iterator

from .model import CrawlEntity, BasicCrawlStats
from ..common.model import DataSource


def load_crawls(ds: DataSource, row_limit: int) -> Iterator[CrawlEntity]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM digilog.digilog.crawl
            LIMIT %s;
            """,
            (row_limit,)
        )
        return map(CrawlEntity.from_record, c.fetchall())


def load_crawl_by_id(ds: DataSource, crawl_id: int) -> CrawlEntity:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM digilog.digilog.crawl
            WHERE id = %s;
            """,
            (crawl_id,)
        )
        result = c.fetchone()
        if not result:
            raise ValueError("Crawl {} does not exist".format(crawl_id))
        return CrawlEntity.from_record(result)


def load_basic_crawl_stats_by_crawl_id(ds: DataSource, crawl_id: int) -> BasicCrawlStats:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            WITH url_amount AS (
                SELECT COUNT(*) as url_amount FROM digilog.digilog.crawl_result
                WHERE crawl_id = %s 
            ),
            crawled_page_amount AS (
                SELECT COUNT(*) as crawled_page_amount FROM digilog.digilog.crawl_result
                WHERE crawl_id = %s AND mongo_id IS NOT NULL
            )
            SELECT * FROM url_amount CROSS JOIN crawled_page_amount
            """,
            (crawl_id, crawl_id)
        )
        result = c.fetchone()
        return BasicCrawlStats.from_record(crawl_id, result)
