from typing import Union, Iterable

from webapp.api.backend.core.common.model import DataSource
from webapp.api.backend.core.repository.model import CrawlQueueEntity, QueueStatus, QueueCrawl


def load_crawl_queue_entry_by_crawl_id(ds: DataSource, crawl_id: int) -> Union[CrawlQueueEntity, None]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * from digilog.digilog.crawling_queue
            WHERE ID = (SELECT queue_id FROM digilog.digilog.queue_crawl WHERE crawl_id = %s)
            """,
            (crawl_id,)
        )
        result = c.fetchone()
        if result:
            return CrawlQueueEntity.from_record(result)
        else:
            return None


def load_crawl_queue_entries(ds: DataSource, row_limit: int) -> Iterable[CrawlQueueEntity]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * from digilog.digilog.crawling_queue
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (row_limit,)
        )
        return map(CrawlQueueEntity.from_record, c.fetchall())


def enqueue_crawl(ds: DataSource, url: str, priority: int) -> CrawlQueueEntity:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            INSERT INTO digilog.crawling_queue (top_url, status, priority, inserted_at, updated_at, reason)
            VALUES (%s, %s, %s, now(), now(), '')
            RETURNING *
            """,
            (url, QueueStatus.NEW.name, priority, )
        )
        return CrawlQueueEntity.from_record(c.fetchone())


def load_queue_crawls(ds: DataSource, queue_ids: Iterable[int]) -> Iterable[QueueCrawl]:
    ids = tuple(queue_ids)
    if len(ids) == 0:
        return []
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT q.*, c.* FROM digilog.crawling_queue as q
            LEFT JOIN digilog.queue_crawl as qc
            ON qc.queue_id = q.id
            LEFT JOIN digilog.crawl as c
            ON c.id = qc.crawl_id
            WHERE q.id IN %s
            """,
            (ids,)
        )
        return map(QueueCrawl.from_record, c.fetchall())
