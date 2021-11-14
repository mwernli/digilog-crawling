from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CrawlEntity:
    id: int
    top_url: str
    inserted_at: datetime

    @staticmethod
    def from_record(record):
        return CrawlEntity(record[0], record[1], record[2])
