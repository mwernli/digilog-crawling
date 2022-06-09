from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


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

    @staticmethod
    def from_record(crawl_id: int, record):
        return BasicCrawlStats(crawl_id, record[0], record[1])


class QueueStatus(Enum):
    NEW = 'NEW'
    PENDING = 'PENDING'
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


@dataclass(frozen=True)
class TranslatedText:
    de: str
    en: str


@dataclass(frozen=True)
class CountryEntity:
    code: str
    name: TranslatedText

    @staticmethod
    def from_record(record):
        return CountryEntity(
            record[0],
            TranslatedText(
                record[2],
                record[1],
            ),
        )


@dataclass(frozen=True)
class StateEntity:
    id: int
    name: str
    country_code: str

    @staticmethod
    def from_record(record):
        return StateEntity(
            record[0],
            record[1],
            record[2],
        )


@dataclass(frozen=True)
class MunicipalityEntity:
    id: int
    name: str
    url: str
    state_id: int

    @staticmethod
    def from_record(record):
        return MunicipalityEntity(
            record[0],
            record[1],
            record[2],
            record[3],
        )


@dataclass(frozen=True)
class QueueCrawl:
    queue_entity: CrawlQueueEntity
    crawl_entity: Optional[CrawlEntity]

    @staticmethod
    def from_named_record(record):
        return QueueCrawl(
            CrawlQueueEntity(
                record.q_id,
                record.q_top_url,
                QueueStatus[record.status],
                record.priority,
                record.q_inserted_at,
                record.updated_at,
                record.reason,
            ),
            CrawlEntity(
                record.c_id,
                record.c_top_url,
                record.c_inserted_at,
            ) if record.c_id is not None else None,
        )
