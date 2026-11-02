from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from library.app.errors import AppError


@dataclass
class GetBookNotFound(AppError):
    id: int

    def __str__(self) -> str:
        return f'Книга с id={self.id} не найдена'


@dataclass(frozen=True)
class GetBookParams:
    id: int


@dataclass(frozen=True)
class ShelfCard:
    hall: str
    rack: int
    shelf: int


@dataclass(frozen=True)
class CopyCard:
    inventory_number: str
    is_available: bool
    shelf: ShelfCard


@dataclass(frozen=True)
class BookCard:
    id: int
    isbn: str
    title: str
    authors: list[str]
    published_year: int
    copies: list[CopyCard] = field(default_factory=list[CopyCard])


class BookCardGateway(ABC):
    @abstractmethod
    def get(self, id: int) -> BookCard | None: ...


class GetBook:
    def __init__(self, gateway: BookCardGateway) -> None:
        self.gateway = gateway

    def run(self, params: GetBookParams) -> BookCard:
        card = self.gateway.get(params.id)
        if card is None:
            raise GetBookNotFound(id=params.id)
        return card
