from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import ClassVar

from classic.criteria import Criteria, criteria
from library.app.commands.domain.errors import DomainError


class LoanPeriodInvalid(DomainError):
    def __str__(self) -> str:
        return 'Срок возврата должен быть позже даты выдачи'


class ExtensionDaysNotPositive(DomainError):
    def __str__(self) -> str:
        return 'Срок продления должен быть положительным'


class ExtensionNotForward(DomainError):
    def __str__(self) -> str:
        return 'Каждое продление должно сдвигать срок вперёд'


@dataclass
class TooManyExtensions(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'У выдачи {self.loan_id} слишком много продлений'


class ReturnedBeforeIssued(DomainError):
    def __str__(self) -> str:
        return 'Дата возврата раньше даты выдачи'


@dataclass
class LoanAlreadyReturned(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'Выдача {self.loan_id} уже возвращена'


@dataclass
class LoanOverdue(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'Выдача {self.loan_id} просрочена'


@dataclass
class LoanNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Выдача с id={self.id} не найдена'


@dataclass(frozen=True)
class LoanPeriod:
    """Объект-значение: срок выдачи."""

    start: date
    due: date

    def check(self) -> None:
        if self.due <= self.start:
            raise LoanPeriodInvalid


@dataclass(frozen=True)
class Extension:
    """Объект-значение: продление выдачи."""

    extended_at: date
    new_due: date

    def check(self) -> None:
        if self.new_due <= self.extended_at:
            raise ExtensionNotForward


@dataclass
class Loan:
    """Корень агрегата."""

    MAX_EXTENSIONS: ClassVar[int] = 2

    reader_id: int  # ссылка на корень агрегата Reader
    book_id: int  # ссылка на корень агрегата Book
    inventory_number: str
    issued_at: date
    period: LoanPeriod
    returned_at: date | None = None
    extensions: list[Extension] = field(default_factory=list[Extension])
    id: int | None = None

    def check(self) -> None:
        self.period.check()
        if len(self.extensions) > self.MAX_EXTENSIONS:
            raise TooManyExtensions(loan_id=self.id)
        previous = self.period.start
        for extension in self.extensions:
            extension.check()
            if extension.new_due <= previous:
                raise ExtensionNotForward
            previous = extension.new_due
        if self.returned_at is not None and self.returned_at < self.issued_at:
            raise ReturnedBeforeIssued

    def extend(self, on: date, days: int) -> None:
        if self.returned():
            raise LoanAlreadyReturned(loan_id=self.id)
        if self.overdue(on=on):
            raise LoanOverdue(loan_id=self.id)
        if days <= 0:
            raise ExtensionDaysNotPositive
        if len(self.extensions) >= self.MAX_EXTENSIONS:
            raise TooManyExtensions(loan_id=self.id)
        new_due = self.period.due + timedelta(days=days)
        self.extensions.append(Extension(extended_at=on, new_due=new_due))
        self.period = LoanPeriod(start=self.period.start, due=new_due)

    def close(self, on: date) -> None:
        if self.returned():
            raise LoanAlreadyReturned(loan_id=self.id)
        if on < self.issued_at:
            raise ReturnedBeforeIssued
        self.returned_at = on

    @criteria
    def overdue(self, on: date) -> bool:
        return self.returned_at is None and self.period.due < on

    @criteria
    def returned(self) -> bool:
        return self.returned_at is not None

    @criteria
    def due_within(self, on: date, days: int) -> bool:
        return self.returned_at is None and on <= self.period.due <= on + timedelta(
            days=days,
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
