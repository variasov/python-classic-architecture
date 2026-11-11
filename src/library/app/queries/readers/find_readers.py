from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import ClassVar


@dataclass(frozen=True)
class FindReadersParams:
    """Параметры списка читателей"""

    MAX_LIMIT: ClassVar[int] = 100

    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.limit <= self.MAX_LIMIT:
            raise ValueError(f'limit должен быть от 1 до {self.MAX_LIMIT}')
        if self.offset < 0:
            raise ValueError('offset не может быть отрицательным')


@dataclass(frozen=True)
class ReaderListItemDTO:
    """Читатель в списке с числом выдач на дату запроса"""

    id: int
    full_name: str
    email: str
    active_loans: int
    overdue_loans: int


class FindReadersGateway(ABC):
    """Список читателей с числом активных и просроченных выдач"""

    @abstractmethod
    def run(
        self, params: FindReadersParams, on: date
    ) -> list[ReaderListItemDTO]: ...


class FindReaders:
    """Список читателей на текущую дату"""

    def __init__(self, gateway: FindReadersGateway) -> None:
        self._gateway = gateway

    def run(self, params: FindReadersParams) -> list[ReaderListItemDTO]:
        on = date.today()
        return self._gateway.run(params, on=on)
