from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Union

from webapp.api.backend.core.repository.model import CrawlQueueEntity


@dataclass(frozen=True)
class CrawlDetail:
    start_url: str
    timestamp: datetime
    url_amount: int
    crawled_pages_amount: int
    stats: Union[dict, None]
    queue_entry: Union[CrawlQueueEntity, None]


class CrawlStatus(Enum):
    NEW = 'NEW'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'
    ERROR = 'ERROR'
    UNKNOWN = 'UNKNOWN'
