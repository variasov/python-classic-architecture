from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogBook:
    isbn: str
    title: str
    authors: list[str]
    year: int


class IsbnCatalog(ABC):
    @abstractmethod
    def find(self, isbn: str) -> CatalogBook | None: ...
