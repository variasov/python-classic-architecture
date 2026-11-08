from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from library.app.clock import Clock


@dataclass(frozen=True)
class FindReadersParams:
    pass


@dataclass(frozen=True)
class ReaderDTO:
    id: int
    full_name: str
    email: str
    phone: str | None
    tier: str
    valid_until: date
    is_blocked: bool
    active_loans: int
    overdue_loans: int


class FindReadersGateway(ABC):
    @abstractmethod
    def find(self, on: date) -> list[ReaderDTO]: ...


class FindReaders:
    def __init__(self, gateway: FindReadersGateway, clock: Clock) -> None:
        self.gateway = gateway
        self.clock = clock

    def run(self, _params: FindReadersParams) -> list[ReaderDTO]:
        return self.gateway.find(on=self.clock.today())
