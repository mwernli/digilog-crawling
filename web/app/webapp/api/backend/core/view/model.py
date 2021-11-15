from dataclasses import dataclass
from datetime import datetime

from ..repository.model import CrawlEntity


@dataclass(frozen=True)
class CrawlOverview:
    id: int
    top_url: str
    inserted_at: datetime

    @staticmethod
    def from_entity(entity: CrawlEntity):
        return CrawlOverview(entity.id, entity.top_url, entity.inserted_at)
