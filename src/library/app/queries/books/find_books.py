from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Literal


@dataclass(frozen=True)
class FindBooksParams:
    """Параметры поиска книг."""

    MAX_LIMIT: ClassVar[int] = 100
    MIN_SEARCH_LENGTH: ClassVar[int] = 3

    title__contains: str | None = None
    author: str | None = None
    only_available: bool = False
    year_from: int | None = None
    year_to: int | None = None
    order_by: Literal['title', 'published_year'] = 'title'
    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.limit <= self.MAX_LIMIT:
            raise ValueError(f'limit должен быть от 1 до {self.MAX_LIMIT}')
        if self.offset < 0:
            raise ValueError('offset не может быть отрицательным')
        search = self.title__contains
        if search is not None and len(search) < self.MIN_SEARCH_LENGTH:
            raise ValueError(
                f'Строка поиска короче {self.MIN_SEARCH_LENGTH} символов',
            )
        if (
            self.year_from is not None
            and self.year_to is not None
            and self.year_from > self.year_to
        ):
            raise ValueError('year_from не может быть больше year_to')


@dataclass(frozen=True)
class BookListItemDTO:
    """Книга в результатах поиска."""

    id: int
    isbn: str
    title: str
    authors: list[str]
    published_year: int
    available_copies: int


class FindBooksGateway(ABC):
    """Поиск книг с фильтрами и пагинацией."""

    @abstractmethod
    def run(self, params: FindBooksParams) -> list[BookListItemDTO]: ...


class FindBooks:
    """Поиск книг."""

    def __init__(self, gateway: FindBooksGateway) -> None:
        self._gateway = gateway

    def run(self, params: FindBooksParams) -> list[BookListItemDTO]:
        return self._gateway.run(params)
