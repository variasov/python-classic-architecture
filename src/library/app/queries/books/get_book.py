from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from library.app.errors import AppError


@dataclass(frozen=True)
class GetBookParams:
    """Параметры карточки книги."""

    id: int


@dataclass(frozen=True)
class BookCopyDTO:
    """Экземпляр в карточке книги вместе с местом на полке."""

    id: int
    inventory_number: str
    hall: str
    rack: int
    shelf: int
    is_available: bool


@dataclass(frozen=True)
class BookCardDTO:
    """Карточка книги с экземплярами."""

    id: int
    isbn: str
    title: str
    authors: list[str]
    published_year: int
    copies: list[BookCopyDTO] = field(
        default_factory=list[BookCopyDTO],
    )


@dataclass
class GetBookNotFound(AppError):
    id: int

    def __str__(self) -> str:
        return f'Книга с id={self.id} не найдена'


class GetBookGateway(ABC):
    """Чтение карточки книги."""

    @abstractmethod
    def run(self, params: GetBookParams) -> BookCardDTO | None: ...


class GetBook:
    """Карточка книги с экземплярами."""

    def __init__(self, gateway: GetBookGateway) -> None:
        self._gateway = gateway

    def run(self, params: GetBookParams) -> BookCardDTO:
        card = self._gateway.run(params)
        if card is None:
            raise GetBookNotFound(id=params.id)
        return card
