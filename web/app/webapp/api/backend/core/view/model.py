from dataclasses import dataclass
from datetime import datetime
from typing import List, Union, Optional

from ..repository.model import CrawlEntity, CrawlQueueEntity, TranslatedText, StateEntity, MunicipalityEntity, \
    QueueCrawl


@dataclass(frozen=True)
class CrawlView:
    id: int
    top_url: str
    inserted_at: datetime

    @staticmethod
    def from_entity(entity: CrawlEntity):
        return CrawlView(entity.id, entity.top_url, entity.inserted_at)


@dataclass(frozen=True)
class CrawlOverview:
    crawl_views: List[CrawlView]


@dataclass(frozen=True)
class CrawlDetailView:
    start_url: str
    timestamp: datetime
    url_amount: int
    crawled_pages_amount: int
    stats: Union[dict, None]
    crawl_status: str
    crawl_duration_seconds: Union[float, None]


@dataclass(frozen=True)
class QueueView:
    id: int
    top_url: str
    status: str
    priority: int
    inserted_at: datetime
    updated_at: datetime
    reason: str
    duration: float

    @staticmethod
    def from_entity(entity: CrawlQueueEntity):
        return QueueView(
            entity.id,
            entity.top_url,
            entity.status.name,
            entity.priority,
            entity.inserted_at,
            entity.updated_at,
            entity.reason,
            queue_entry_duration(entity),
        )


@dataclass(frozen=True)
class QueueOverview:
    queue_views: List[QueueView]


def queue_entry_duration(entry: CrawlQueueEntity) -> float:
    print(entry.status)
    return (entry.updated_at - entry.inserted_at).total_seconds()


@dataclass(frozen=True)
class CountryDetailView:
    code: str
    name: TranslatedText
    states: List[StateEntity]


@dataclass(frozen=True)
class StateDetailView:
    entity: StateEntity
    municipalities: List[MunicipalityEntity]


@dataclass(frozen=True)
class QueueCrawlView:
    queue_view: QueueView
    crawl_entity: Optional[CrawlEntity]

    @staticmethod
    def from_queue_crawl(queue_crawl: QueueCrawl):
        return QueueCrawlView(
            QueueView.from_entity(queue_crawl.queue_entity),
            queue_crawl.crawl_entity,
        )


@dataclass(frozen=True)
class MunicipalityDetailView:
    entity: MunicipalityEntity
    queue_crawls: List[QueueCrawlView]
