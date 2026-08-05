from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class ThingDTO:
    """Пример DTO"""
    id: UUID
    items_count: int


class SearchThings(ABC):
    """Пример usecase-запроса"""

    @abstractmethod
    def run(
        self,
        items__len__le: int | None = None,
        items__len__ge: int | None = None,
        very_useful_field__contains: str | None = None,
    ) -> list[ThingDTO]:
        ...
