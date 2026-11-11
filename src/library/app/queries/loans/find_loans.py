from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import ClassVar


@dataclass(frozen=True)
class FindLoansParams:
    """Параметры списка выдач"""

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
class LoanListItemDTO:
    """Выдача в списке"""

    id: int
    reader_id: int
    copy_id: int
    start: date
    due: date
    returned_at: date | None
    extensions_count: int


class FindLoansGateway(ABC):
    """Список выдач с фильтрами на дату запроса"""

    @abstractmethod
    def run(
        self, params: FindLoansParams, on: date
    ) -> list[LoanListItemDTO]: ...


class FindLoans:
    """Список выдач на текущую дату"""

    def __init__(self, gateway: FindLoansGateway) -> None:
        self._gateway = gateway

    def run(self, params: FindLoansParams) -> list[LoanListItemDTO]:
        on = date.today()
        return self._gateway.run(params, on=on)
