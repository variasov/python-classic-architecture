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


class FindCats(ABC):

    @abstractmethod
    def run(self, age_from: int, age_to: int) -> list[CatDTO]:
        ...
