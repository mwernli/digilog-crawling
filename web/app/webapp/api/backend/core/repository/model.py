from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class CrawlEntity:
    id: int
    top_url: str
    inserted_at: datetime

    @staticmethod
    def from_record(record):
        return CrawlEntity(record[0], record[2], record[1])


@dataclass(frozen=True)
class BasicCrawlStats:
    crawl_id: int
    url_amount: int
    crawled_pages_amount: int
    timedelta: float

    @staticmethod
    def from_record(crawl_id: int, record):
        return BasicCrawlStats(crawl_id, record[0], record[1], record[2].seconds)


class QueueStatus(Enum):
    NEW = 'NEW'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'
    ERROR = 'ERROR'


@dataclass(frozen=True)
class CrawlQueueEntity:
    id: int
    top_url: str
    status: QueueStatus
    priority: int
    inserted_at: datetime
    updated_at: datetime
    reason: str

    @staticmethod
    def from_record(record):
        return CrawlQueueEntity(
            record[0],
            record[1],
            QueueStatus[record[2]],
            record[3],
            record[4],
            record[5],
            record[6],
        )
