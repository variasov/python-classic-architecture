from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Literal


@dataclass(frozen=True)
class FindBooksParams:
    MAX_LIMIT: ClassVar[int] = 100
    MIN_SEARCH_LENGTH: ClassVar[int] = 3

    title__contains: str | None = None
    author: str | None = None
    only_available: bool = False
    year_from: int | None = None
    year_to: int | None = None
    sort_by: Literal['title', 'published_year', 'id'] = 'title'
    sort_order: Literal['asc', 'desc'] = 'asc'
    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.limit <= self.MAX_LIMIT:
            raise ValueError(
                f'limit должен быть от 1 до {self.MAX_LIMIT}',
            )
        if self.offset < 0:
            raise ValueError('offset не может быть отрицательным')
        if (
            self.year_from is not None
            and self.year_to is not None
            and self.year_from > self.year_to
        ):
            raise ValueError('year_from не может быть больше year_to')


@dataclass(frozen=True)
class BookDTO:
    id: int
    isbn: str
    title: str
    authors: list[str]
    published_year: int


class FindBooksGateway(ABC):
    @abstractmethod
    def find(self, params: FindBooksParams) -> list[BookDTO]: ...


class FindBooks:
    def __init__(self, gateway: FindBooksGateway) -> None:
        self.gateway = gateway

    def run(self, params: FindBooksParams) -> list[BookDTO]:
        search = params.title__contains
        if search is not None and len(search) < params.MIN_SEARCH_LENGTH:
            return []
        return self.gateway.find(params)
