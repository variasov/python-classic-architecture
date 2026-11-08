from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from library.app.errors import AppError


@dataclass(frozen=True)
class GetBookParams:
    id: int


@dataclass(frozen=True)
class CopyDTO:
    inventory_number: str
    hall: str
    rack: int
    shelf: int
    is_available: bool


@dataclass(frozen=True)
class GetBookDTO:
    id: int
    isbn: str
    title: str
    authors: list[str]
    published_year: int
    copies: list[CopyDTO] = field(default_factory=list[CopyDTO])


@dataclass
class GetBookNotFound(AppError):
    id: int

    def __str__(self) -> str:
        return f'Книга с id={self.id} не найдена'


class GetBookGateway(ABC):
    @abstractmethod
    def get(self, id: int) -> GetBookDTO | None: ...


class GetBook:
    def __init__(self, gateway: GetBookGateway) -> None:
        self.gateway = gateway

    def run(self, params: GetBookParams) -> GetBookDTO:
        book = self.gateway.get(params.id)
        if book is None:
            raise GetBookNotFound(id=params.id)
        return book
