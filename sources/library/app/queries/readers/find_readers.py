from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from library.app.clock import Clock


@dataclass(frozen=True)
class FindReadersParams:
    MAX_LIMIT: ClassVar[int] = 100

    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.limit <= self.MAX_LIMIT:
            raise ValueError(f'limit должен быть от 1 до {self.MAX_LIMIT}')
        if self.offset < 0:
            raise ValueError('offset не может быть отрицательным')


@dataclass(frozen=True)
class FoundReader:
    id: int
    full_name: str
    email: str
    tier: str
    valid_until: date
    is_blocked: bool
    active_loans: int
    overdue_loans: int


class ReadersSearchGateway(ABC):
    @abstractmethod
    def find(self, params: FindReadersParams, today: date) -> list[FoundReader]: ...


class FindReaders:
    def __init__(self, gateway: ReadersSearchGateway, clock: Clock) -> None:
        self.gateway = gateway
        self.clock = clock

    def run(self, params: FindReadersParams) -> list[FoundReader]:
        return self.gateway.find(params, self.clock.today())
