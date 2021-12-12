from dataclasses import dataclass
from datetime import datetime
from typing import List, Union

from ..repository.model import CrawlEntity, CrawlQueueEntity


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
    print(entry.updated_at)
    print(entry.inserted_at)
    return (entry.updated_at - entry.inserted_at).total_seconds()
