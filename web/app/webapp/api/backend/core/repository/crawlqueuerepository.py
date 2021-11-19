from typing import Union

from webapp.api.backend.core.common.model import DataSource
from webapp.api.backend.core.repository.model import CrawlQueueEntity


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
