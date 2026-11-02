from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from library.app.clock import Clock


@dataclass(frozen=True)
class FindLoansParams:
    MAX_LIMIT: ClassVar[int] = 100

    reader_id: int | None = None
    only_overdue: bool = False
    only_active: bool = False
    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.limit <= self.MAX_LIMIT:
            raise ValueError(f'limit должен быть от 1 до {self.MAX_LIMIT}')
        if self.offset < 0:
            raise ValueError('offset не может быть отрицательным')


@dataclass(frozen=True)
class FoundLoan:
    id: int
    reader_id: int
    book_id: int
    inventory_number: str
    issued_at: date
    due: date
    returned_at: date | None
    extensions_count: int


class LoansSearchGateway(ABC):
    @abstractmethod
    def find(self, params: FindLoansParams, today: date) -> list[FoundLoan]: ...


class FindLoans:
    def __init__(self, gateway: LoansSearchGateway, clock: Clock) -> None:
        self.gateway = gateway
        self.clock = clock

    def run(self, params: FindLoansParams) -> list[FoundLoan]:
        return self.gateway.find(params, self.clock.today())
