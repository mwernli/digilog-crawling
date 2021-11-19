from dataclasses import asdict
from typing import Union

from .model import CrawlOverview, CrawlOverviews, CrawlDetailView
from ..application.service import load_all_crawls, load_crawl_details, determine_crawl_status, \
    determine_crawl_duration_seconds
from ..common.model import DataSource


def get_crawl_overview(ds: DataSource, row_limit: int) -> CrawlOverviews:
    overviews = map(CrawlOverview.from_entity, load_all_crawls(ds, row_limit))
    return CrawlOverviews(list(overviews))


def get_crawl_detail(ds: DataSource, crawl_id: int) -> CrawlDetailView:
    crawl_detail = load_crawl_details(ds, crawl_id)
    crawl_status = determine_crawl_status(crawl_detail)
    crawl_duration_seconds = determine_crawl_duration_seconds(crawl_detail)
    return CrawlDetailView(
        crawl_detail.start_url,
        crawl_detail.timestamp,
        crawl_detail.url_amount,
        crawl_detail.crawled_pages_amount,
        crawl_detail.stats,
        crawl_status.name,
        crawl_duration_seconds,
    )

