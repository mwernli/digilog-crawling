from typing import Iterator

from .model import CrawlDetail, CrawlStatus
from ..common.model import DataSource
from ..repository.crawlqueuerepository import load_crawl_queue_entry_by_crawl_id
from ..repository.crawlrepository import load_crawls, load_crawl_by_id, load_basic_crawl_stats_by_crawl_id
from ..repository.model import CrawlEntity
from ..repository.statsrepository import load_stats_for_crawl_id


def load_all_crawls(ds: DataSource, row_limit: int) -> Iterator[CrawlEntity]:
    return load_crawls(ds, row_limit)


def load_crawl_details(ds: DataSource, crawl_id: int) -> CrawlDetail:
    crawl_entity = load_crawl_by_id(ds, crawl_id)
    crawl_basic_stats = load_basic_crawl_stats_by_crawl_id(ds, crawl_id)
    crawl_stats = load_stats_for_crawl_id(ds, crawl_id)
    queue_entry = load_crawl_queue_entry_by_crawl_id(ds, crawl_id)
    return CrawlDetail(
        crawl_entity.top_url,
        crawl_entity.inserted_at,
        crawl_basic_stats.url_amount,
        crawl_basic_stats.crawled_pages_amount,
        crawl_basic_stats.timedelta,
        crawl_stats,
        queue_entry,
    )


def determine_crawl_status(crawl_detail: CrawlDetail) -> CrawlStatus:
    if crawl_detail.queue_entry is not None:
        return CrawlStatus[crawl_detail.queue_entry.status]
    elif crawl_detail.stats is not None:
        return CrawlStatus.DONE
    else:
        return CrawlStatus.UNKNOWN


def determine_crawl_duration_seconds(crawl_detail: CrawlDetail) -> float:
    if crawl_detail.queue_entry is not None and crawl_detail.queue_entry.status != 'IN_PROGRESS':
        return (crawl_detail.queue_entry.updated_at - crawl_detail.queue_entry.inserted_at).total_seconds()
    else:
        return crawl_detail.time_delta

