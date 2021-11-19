from dataclasses import dataclass
from datetime import datetime
from typing import List, Union

from ..repository.model import CrawlEntity


@dataclass(frozen=True)
class CrawlOverview:
    id: int
    top_url: str
    inserted_at: datetime

    @staticmethod
    def from_entity(entity: CrawlEntity):
        return CrawlOverview(entity.id, entity.top_url, entity.inserted_at)


@dataclass(frozen=True)
class CrawlOverviews:
    crawl_overviews: List[CrawlOverview]


@dataclass(frozen=True)
class CrawlDetailView:
    start_url: str
    timestamp: datetime
    url_amount: int
    crawled_pages_amount: int
    stats: Union[dict, None]
    crawl_status: str
    crawl_duration_seconds: Union[float, None]


