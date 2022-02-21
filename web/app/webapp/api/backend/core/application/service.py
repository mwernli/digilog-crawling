from datetime import datetime
from typing import Iterable

from .model import CrawlDetail, CrawlStatus
from ..common.model import DataSource
from ..repository import placerepository, crawlqueuerepository
from ..repository.crawlqueuerepository import load_crawl_queue_entry_by_crawl_id, load_crawl_queue_entries
from ..repository.crawlrepository import load_crawls, load_crawl_by_id, load_basic_crawl_stats_by_crawl_id
from ..repository.model import CrawlEntity, CrawlQueueEntity, CountryEntity, StateEntity, MunicipalityEntity, \
    QueueCrawl, QueueStatus
from ..repository.statsrepository import load_stats_for_crawl_id


def load_all_crawls(ds: DataSource, row_limit: int) -> Iterable[CrawlEntity]:
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
        crawl_stats,
        queue_entry,
    )


def determine_crawl_status(crawl_detail: CrawlDetail) -> CrawlStatus:
    if crawl_detail.queue_entry is not None:
        return CrawlStatus[crawl_detail.queue_entry.status.name]
    elif crawl_detail.stats is not None:
        return CrawlStatus.DONE
    else:
        return CrawlStatus.UNKNOWN


def determine_crawl_duration_seconds(crawl_detail: CrawlDetail) -> float:
    if crawl_detail.queue_entry is not None and crawl_detail.queue_entry.status != QueueStatus.IN_PROGRESS:
        return (crawl_detail.queue_entry.updated_at - crawl_detail.timestamp).total_seconds()
    else:
        return (datetime.now() - crawl_detail.timestamp).total_seconds()


def load_all_crawl_queue_entries(ds: DataSource, row_limit: int) -> Iterable[CrawlQueueEntity]:
    return load_crawl_queue_entries(ds, row_limit)


def load_all_countries(ds: DataSource) -> Iterable[CountryEntity]:
    return placerepository.list_all_countries(ds)


def load_country_by_code(ds: DataSource, country_code: str) -> CountryEntity:
    return placerepository.get_country_by_code(ds, country_code)


def load_states_of_country(ds: DataSource, country_code: str) -> Iterable[StateEntity]:
    return placerepository.load_states_of_country(ds, country_code)


def get_state_by_id(ds: DataSource, state_id: int) -> StateEntity:
    return placerepository.get_state_by_id(ds, state_id)


def load_municipalities_of_state(ds: DataSource, state_id: int) -> Iterable[MunicipalityEntity]:
    return placerepository.load_municipalities_of_state(ds, state_id)


def get_municipality_by_id(ds: DataSource, municipality_id: int) -> MunicipalityEntity:
    return placerepository.get_municipality_by_id(ds, municipality_id)


def update_municipality(ds: DataSource, municipality_id: int, url: str) -> MunicipalityEntity:
    return placerepository.update_municipality(ds, municipality_id, url)


def enqueue_municipality_crawl(ds: DataSource, municipality_id: int) -> MunicipalityEntity:
    municipality = get_municipality_by_id(ds, municipality_id)
    queue_entry = crawlqueuerepository.enqueue_crawl(ds, municipality.url, 0)
    placerepository.add_municipality_queue_connection(ds, municipality_id, queue_entry.id)
    return municipality


def get_municipality_queue_crawls(ds: DataSource, municipality_id: int) -> Iterable[QueueCrawl]:
    queue_ids = placerepository.load_municipality_queue_ids(ds, municipality_id)
    return crawlqueuerepository.load_queue_crawls(ds, queue_ids)
