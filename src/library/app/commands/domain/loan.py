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
        return f'Срок выдачи {self.due} должен быть позже начала {self.start}'


@dataclass
class TooManyExtensions(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'У выдачи с id={self.loan_id} слишком много продлений'


@dataclass
class ExtensionNotForward(DomainError):
    loan_id: int | None
    new_due: date

    def __str__(self) -> str:
        return (
            f'Продление выдачи с id={self.loan_id} не сдвигает срок '
            f'вперёд (новый срок {self.new_due})'
        )


@dataclass
class ExtensionsInconsistent(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'История продлений выдачи с id={self.loan_id} противоречива'


@dataclass
class ReturnBeforeIssue(DomainError):
    loan_id: int | None
    issued_at: date
    returned_at: date

    def __str__(self) -> str:
        return (
            f'Выдача с id={self.loan_id} возвращена {self.returned_at} '
            f'раньше выдачи {self.issued_at}'
        )


@dataclass
class LoanAlreadyReturned(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'Выдача с id={self.loan_id} уже возвращена'


@dataclass
class LoanOverdue(DomainError):
    loan_id: int | None

    def __str__(self) -> str:
        return f'Просроченную выдачу с id={self.loan_id} нельзя продлить'


class ExtensionDaysNotPositive(DomainError):
    def __str__(self) -> str:
        return 'Срок продления должен быть положительным'


@dataclass
class LoanNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Выдача с id={self.id} не найдена'


@dataclass(frozen=True)
class LoanPeriod:
    start: date
    due: date

    def check(self) -> None:
        if self.due <= self.start:
            raise LoanPeriodInvalid(start=self.start, due=self.due)

    def extended(self, days: int) -> 'LoanPeriod':
        return LoanPeriod(
            start=self.start,
            due=self.due + timedelta(days=days),
        )


@dataclass(frozen=True)
class Extension:
    extended_at: date
    new_due: date


@dataclass
class Loan:
    MAX_EXTENSIONS: ClassVar[int] = 2

    reader_id: int
    book_id: int
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
        previous_due = self.period.start
        for extension in self.extensions:
            if extension.new_due <= previous_due:
                raise ExtensionNotForward(
                    loan_id=self.id,
                    new_due=extension.new_due,
                )
            previous_due = extension.new_due
        if self.extensions and self.extensions[-1].new_due != self.period.due:
            raise ExtensionsInconsistent(loan_id=self.id)
        if self.returned_at is not None and self.returned_at < self.issued_at:
            raise ReturnBeforeIssue(
                loan_id=self.id,
                issued_at=self.issued_at,
                returned_at=self.returned_at,
            )

    def extend(self, on: date, days: int) -> None:
        if self.returned_at is not None:
            raise LoanAlreadyReturned(loan_id=self.id)
        if self.overdue(on=on):
            raise LoanOverdue(loan_id=self.id)
        if days <= 0:
            raise ExtensionDaysNotPositive
        if len(self.extensions) >= self.MAX_EXTENSIONS:
            raise TooManyExtensions(loan_id=self.id)
        new_period = self.period.extended(days)
        self.extensions.append(
            Extension(extended_at=on, new_due=new_period.due),
        )
        self.period = new_period

    def close(self, on: date) -> None:
        if self.returned_at is not None:
            raise LoanAlreadyReturned(loan_id=self.id)
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
    def belongs_to_reader(self, reader_id: int) -> bool:
        return self.reader_id == reader_id


class LoansRepo(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Loan: ...

    @abstractmethod
    def save(self, loan: Loan) -> Loan: ...

    @abstractmethod
    def find(self, criteria: Criteria[Loan]) -> list[Loan]: ...
