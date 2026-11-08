from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from library.app.clock import Clock


@dataclass(frozen=True)
class FindLoansParams:
    reader_id: int | None = None
    only_overdue: bool = False
    only_active: bool = False


@dataclass(frozen=True)
class LoanDTO:
    id: int
    reader_id: int
    book_id: int
    inventory_number: str
    issued_at: date
    due: date
    returned_at: date | None
    extensions_count: int


class FindLoansGateway(ABC):
    @abstractmethod
    def find(
        self,
        params: FindLoansParams,
        on: date,
    ) -> list[LoanDTO]: ...


class FindLoans:
    def __init__(self, gateway: FindLoansGateway, clock: Clock) -> None:
        self.gateway = gateway
        self.clock = clock

    def run(self, params: FindLoansParams) -> list[LoanDTO]:
        return self.gateway.find(params=params, on=self.clock.today())
