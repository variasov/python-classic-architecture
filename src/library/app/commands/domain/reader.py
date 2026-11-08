from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from classic.criteria import Criteria, criteria

from library.app.commands.domain.errors import DomainError


class ReaderNameEmpty(DomainError):
    def __str__(self) -> str:
        return 'ФИО читателя не может быть пустым'


@dataclass
class ContactEmailInvalid(DomainError):
    email: str

    def __str__(self) -> str:
        return f'Email {self.email!r} должен содержать символ @'


@dataclass
class MembershipTierInvalid(DomainError):
    tier: str

    def __str__(self) -> str:
        return f'Неизвестный тариф членства {self.tier!r}'


@dataclass
class ReaderNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Читатель с id={self.id} не найден'


@dataclass
class ReaderCannotBorrow(DomainError):
    reader_id: int | None

    def __str__(self) -> str:
        return f'Читатель с id={self.reader_id} не может брать книги'


@dataclass
class LoanLimitExceeded(DomainError):
    reader_id: int | None
    limit: int

    def __str__(self) -> str:
        return (
            f'Читатель с id={self.reader_id} уже взял максимум '
            f'({self.limit}) книг по своему тарифу'
        )


@dataclass
class ReaderHasOverdueLoans(DomainError):
    reader_id: int | None

    def __str__(self) -> str:
        return f'У читателя с id={self.reader_id} есть просроченные выдачи'


@dataclass(frozen=True)
class Contact:
    email: str
    phone: str | None = None

    def check(self) -> None:
        if '@' not in self.email:
            raise ContactEmailInvalid(email=self.email)


@dataclass(frozen=True)
class Membership:
    LOAN_LIMITS: ClassVar[dict[str, int]] = {'basic': 3, 'premium': 10}

    tier: str
    valid_until: date

    def check(self) -> None:
        if self.tier not in self.LOAN_LIMITS:
            raise MembershipTierInvalid(tier=self.tier)

    @property
    def loan_limit(self) -> int:
        return self.LOAN_LIMITS[self.tier]


@dataclass
class Reader:
    full_name: str
    contact: Contact
    membership: Membership
    is_blocked: bool = False
    id: int | None = None

    def check(self) -> None:
        if not self.full_name.strip():
            raise ReaderNameEmpty
        self.contact.check()
        self.membership.check()

    def extend_membership(self, until: date) -> None:
        self.membership = Membership(
            tier=self.membership.tier,
            valid_until=until,
        )

    def block(self) -> None:
        self.is_blocked = True

    def unblock(self) -> None:
        self.is_blocked = False

    @criteria
    def membership_active(self, on: date) -> bool:
        return self.membership.valid_until >= on

    @criteria
    def has_tier(self, tier: str) -> bool:
        return self.membership.tier == tier

    @criteria
    def not_blocked(self) -> bool:
        return not self.is_blocked


class ReadersRepo(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Reader: ...

    @abstractmethod
    def save(self, reader: Reader) -> Reader: ...

    @abstractmethod
    def find(self, criteria: Criteria[Reader]) -> list[Reader]: ...
