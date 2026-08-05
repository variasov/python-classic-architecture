from abc import ABC, abstractmethod
from dataclasses import dataclass

from demo.app.commands.domain.aggregates.cat import Movement


@dataclass
class CatDTO:
    id: str
    name: str
    age: int
    mood: str
    movements: list[Movement]


class GetCat(ABC):

    @abstractmethod
    def run(self, cat_id: str) -> CatDTO | None:
        ...
