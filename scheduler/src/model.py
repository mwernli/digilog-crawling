import datetime
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional


@dataclass(eq=True, frozen=True)
class Municipality:
    id: int
    name_de: str
    url: str
    population: Optional[int]
    area: Optional[int]

    @staticmethod
    def from_named_tuple(r: namedtuple):
        return Municipality(r.id, r.name_de, r.url, r.population, r.area_sqm)


@dataclass(eq=True, frozen=True)
class CalibrationRun:
    municipality: Municipality
    queue_id: int
    crawl_id: int
    stats_id: str
    calibration_id: int
    settings_key: str


@dataclass(eq=True, frozen=True)
class UrlCheck:
    municipality_id: int
    url: str
    last_check: Optional[datetime.datetime]
    outcome: Optional[str]
    attempts: Optional[int]


@dataclass(eq=True, frozen=True)
class UrlCheckResult:
    municipality_id: int
    original_url: str
    updated_url: str
    outcome: str
    attempts: int

    def url_changed(self) -> bool:
        return self.original_url != self.updated_url

    def too_many_attempts(self, max_retries: int):
        return self.outcome == 'ERROR' and self.attempts >= max_retries
