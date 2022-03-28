from typing import List, Dict

from .model import CrawlView, CrawlOverview, CrawlDetailView, QueueOverview, CountryDetailView, \
    StateDetailView, MunicipalityDetailView, QueueCrawlView
from ..application import service
from ..common.model import DataSource
from ..repository.model import CountryEntity, StateEntity, MunicipalityEntity


def get_crawl_overview(ds: DataSource, row_limit: int) -> CrawlOverview:
    overviews = map(CrawlView.from_entity, service.load_all_crawls(ds, row_limit))
    return CrawlOverview(list(overviews))


def get_crawl_detail(ds: DataSource, crawl_id: int) -> CrawlDetailView:
    crawl_detail = service.load_crawl_details(ds, crawl_id)
    crawl_status = service.determine_crawl_status(crawl_detail)
    crawl_duration_seconds = service.determine_crawl_duration_seconds(crawl_detail)
    return CrawlDetailView(
        crawl_detail.start_url,
        crawl_detail.timestamp,
        crawl_detail.url_amount,
        crawl_detail.crawled_pages_amount,
        crawl_detail.stats,
        crawl_status.name,
        crawl_duration_seconds,
    )


def get_queue_overview(ds: DataSource, row_limit: int) -> QueueOverview:
    queue_crawls = service.load_queue_crawls_with_limit(ds, row_limit)
    return QueueOverview(list(map(QueueCrawlView.from_queue_crawl, queue_crawls)))


def get_all_countries(ds: DataSource) -> List[CountryEntity]:
    return list(service.load_all_countries(ds))


def get_country_detail_view(ds: DataSource, country_code: str) -> CountryDetailView:
    country_entity = service.load_country_by_code(ds, country_code)
    states = list(service.load_states_of_country(ds, country_code))
    return CountryDetailView(
        country_entity.code,
        country_entity.name,
        states,
    )


def get_states_of_country(ds: DataSource, country_code: str) -> List[StateEntity]:
    return list(service.load_states_of_country(ds, country_code))


def get_state_detail_view(ds: DataSource, state_id: int) -> StateDetailView:
    return StateDetailView(
        service.get_state_by_id(ds, state_id),
        list(service.load_municipalities_of_state(ds, state_id)),
    )


def get_municipality_detail_view(ds: DataSource, municipality_id: int) -> MunicipalityDetailView:
    return build_municipality_view_details(
        ds,
        service.get_municipality_by_id(ds, municipality_id),
    )


def update_municipality(ds: DataSource, municipality_id: int, update_data: Dict) -> MunicipalityDetailView:
    return build_municipality_view_details(
        ds,
        service.update_municipality(ds, municipality_id, update_data['url']),
    )


def enqueue_municipality_crawl(ds: DataSource, municipality_id: int) -> MunicipalityDetailView:
    return build_municipality_view_details(
        ds,
        service.enqueue_municipality_crawl(ds, municipality_id),
    )


def build_municipality_view_details(ds: DataSource, entity: MunicipalityEntity) -> MunicipalityDetailView:
    queue_crawls = service.get_municipality_queue_crawls(ds, entity.id)
    return MunicipalityDetailView(
        entity,
        list(map(QueueCrawlView.from_queue_crawl, queue_crawls)),
    )


