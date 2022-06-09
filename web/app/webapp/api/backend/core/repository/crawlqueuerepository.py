import json
from typing import Union, Iterable

from webapp.api.backend.core.common.model import DataSource
from webapp.api.backend.core.repository.model import CrawlQueueEntity, QueueStatus, QueueCrawl


def load_crawl_queue_entry_by_crawl_id(ds: DataSource, crawl_id: int) -> Union[CrawlQueueEntity, None]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT * FROM crawling_queue
            WHERE ID = (SELECT queue_id FROM queue_crawl WHERE crawl_id = %s)
            """,
            (crawl_id,)
        )
        result = c.fetchone()
        if result:
            return CrawlQueueEntity.from_record(result)
        else:
            return None


def enqueue_crawl(ds: DataSource, url: str, priority: int, crawl_type: str, settings: dict) -> CrawlQueueEntity:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            INSERT INTO crawling_queue (
                top_url,
                status,
                priority,
                inserted_at,
                updated_at,
                reason,
                crawl_type,
                scrapy_settings
            )
            VALUES (%s, %s, %s, NOW(), NOW(), '', %s, %s)
            RETURNING *
            """,
            (url, QueueStatus.NEW.name, priority, crawl_type, json.dumps(settings),)
        )
        return CrawlQueueEntity.from_record(c.fetchone())


def load_queue_crawls_of_queue_ids(ds: DataSource, queue_ids: Iterable[int]) -> Iterable[QueueCrawl]:
    ids = tuple(queue_ids)
    if len(ids) == 0:
        return []
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT
            q.id AS q_id,
            q.top_url AS q_top_url,
            q.status,
            q.priority,
            q.inserted_at AS q_inserted_at,
            q.updated_at,
            q.reason,
            c.id AS c_id,
            c.inserted_at AS c_inserted_at,
            c.top_url AS c_top_url
            FROM crawling_queue AS q
            LEFT JOIN queue_crawl AS qc
            ON qc.queue_id = q.id
            LEFT JOIN crawl AS c
            ON c.id = qc.crawl_id
            WHERE q.id IN %s
            """,
            (ids,)
        )
        return map(QueueCrawl.from_named_record, c.fetchall())


def load_queue_crawls_with_limit(ds: DataSource, row_limit: int) -> Iterable[QueueCrawl]:
    with ds.postgres_cursor() as c:
        c.execute(
            """
            SELECT
            q.id AS q_id,
            q.top_url AS q_top_url,
            q.status,
            q.priority,
            q.inserted_at AS q_inserted_at,
            q.updated_at,
            q.reason,
            c.id AS c_id,
            c.inserted_at AS c_inserted_at,
            c.top_url AS c_top_url
            FROM crawling_queue AS q
            LEFT JOIN queue_crawl AS qc
            ON qc.queue_id = q.id
            LEFT JOIN crawl AS c
            ON c.id = qc.crawl_id
            LIMIT %s
            """,
            (row_limit,)
        )
        return map(QueueCrawl.from_named_record, c.fetchall())
