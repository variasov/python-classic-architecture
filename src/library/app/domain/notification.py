from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from enum import Enum

from classic.criteria import Criteria, criteria

from library.app.domain.errors import DomainError


class NotificationKind(Enum):
    """Вид уведомления читателю."""

    loan_issued = 'loan_issued'
    loan_overdue = 'loan_overdue'


@dataclass
class NotificationNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Уведомление с id={self.id} не найдено'


@dataclass
class Notification:
    """Корень агрегата: уведомление для читателя."""

    reader_id: int
    loan_id: int
    kind: NotificationKind
    created_at: date
    id: int | None = None

    def check(self) -> None:
        """У уведомления нет собственных инвариантов."""

    @criteria
    def about_loan(self, loan_id: int) -> bool:
        return self.loan_id == loan_id

    @criteria
    def of_kind(self, kind: NotificationKind) -> bool:
        return self.kind == kind


class NotificationsRepo(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Notification: ...

    @abstractmethod
    def save(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def find(self, criteria: Criteria[Notification]) -> list[Notification]: ...
