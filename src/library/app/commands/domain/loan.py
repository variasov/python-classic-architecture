from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import ClassVar

from classic.criteria import Criteria, criteria

from library.app.commands.domain.errors import DomainError


@dataclass
class LoanPeriodInvalid(DomainError):
    start: date
    due: date

    def __str__(self) -> str:
        return f'Срок выдачи задан неверно: начало={self.start}, конец={self.due}'


@dataclass
class TooManyExtensions(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'У выдачи с id={self.loan_id} слишком много продлений'


@dataclass
class ExtensionNotForward(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'Продление выдачи с id={self.loan_id} не сдвигает срок вперёд'


@dataclass
class LoanReturnedBeforeIssue(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'Выдача с id={self.loan_id} возвращена раньше даты выдачи'


@dataclass
class LoanNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Выдача с id={self.id} не найдена'


@dataclass(frozen=True)
class LoanPeriod:
    """Объект-значение: срок выдачи"""

    start: date
    due: date

    def check(self) -> None:
        if self.due <= self.start:
            raise LoanPeriodInvalid(start=self.start, due=self.due)


@dataclass(frozen=True)
class Extension:
    """Объект-значение: продление выдачи"""

    extended_at: date
    new_due: date


@dataclass
class Loan:
    """Корень агрегата: выдача экземпляра читателю"""

    TERM_DAYS: ClassVar[int] = 14
    MAX_EXTENSIONS: ClassVar[int] = 2

    reader_id: int
    copy_id: int
    period: LoanPeriod
    returned_at: date | None = None
    extensions: list[Extension] = field(default_factory=list[Extension])
    id: int | None = None

    def check(self) -> None:
        self.period.check()
        if len(self.extensions) > self.MAX_EXTENSIONS:
            raise TooManyExtensions(loan_id=self.id)
        previous_due = self.period.due
        for extension in self.extensions:
            if extension.new_due <= previous_due:
                raise ExtensionNotForward(loan_id=self.id)
            previous_due = extension.new_due
        if self.returned_at is not None and self.returned_at < self.period.start:
            raise LoanReturnedBeforeIssue(loan_id=self.id)

    @criteria
    def overdue(self, on: date) -> bool:
        return self.returned_at is None and self.period.due < on

    @criteria
    def returned(self) -> bool:
        return self.returned_at is not None

    @criteria
    def due_within(self, on: date, days: int) -> bool:
        return (
            self.returned_at is None
            and on <= self.period.due <= on + timedelta(days=days)
        )

    @criteria
    def of_reader(self, reader_id: int) -> bool:
        return self.reader_id == reader_id


class LoansRepo(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Loan: ...

    @abstractmethod
    def save(self, loan: Loan) -> Loan: ...

    @abstractmethod
    def find(self, criteria: Criteria[Loan]) -> list[Loan]: ...
