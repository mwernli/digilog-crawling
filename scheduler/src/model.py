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
        return Municipality(r.id, r.name_de, r.url, r.population, r.area)


@dataclass(eq=True, frozen=True)
class CalibrationRun:
    municipality: Municipality
    queue_id: int
    crawl_id: int
    stats_id: str
