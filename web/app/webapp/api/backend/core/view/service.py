from dataclasses import asdict
from typing import List, Iterator

from .model import CrawlOverview
from ..application.service import load_all_crawls
from ..common.model import DataSource


def get_crawl_overview(ds: DataSource) -> dict:
    return crawl_overview_response(map(CrawlOverview.from_entity, load_all_crawls(ds)))


def crawl_overview_response(crawl_overviews: Iterator[CrawlOverview]) -> dict:
    return {
        'data': list(map(asdict, crawl_overviews))
    }


