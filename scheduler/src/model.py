from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class Municipality:
    id: int
    name_de: str
    url: str
