from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import date
from typing import ClassVar

from classic.criteria import Criteria, criteria
from library.app.commands.domain.errors import DomainError


class FullNameEmpty(DomainError):
    def __str__(self) -> str:
        return 'ФИО читателя не может быть пустым'


class InvalidEmail(DomainError):
    def __str__(self) -> str:
        return 'Email должен содержать @'


@dataclass
class InvalidTier(DomainError):
    tier: str

    def __str__(self) -> str:
        return f'Неизвестный тариф {self.tier}'


@dataclass
class MembershipNotExtended(DomainError):
    valid_until: date
    until: date

    def __str__(self) -> str:
        return f'Новая дата {self.until} не позже текущей {self.valid_until}'


@dataclass
class ReaderNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Читатель с id={self.id} не найден'


@dataclass(frozen=True)
class Contact:
    """Объект-значение: контакты читателя."""

    email: str
    phone: str | None = None

    def check(self) -> None:
        if '@' not in self.email:
            raise InvalidEmail


@dataclass(frozen=True)
class Membership:
    """Объект-значение: членство."""

    LOAN_LIMITS: ClassVar[dict[str, int]] = {'basic': 3, 'premium': 10}

    tier: str
    valid_until: date

    def check(self) -> None:
        if self.tier not in self.LOAN_LIMITS:
            raise InvalidTier(tier=self.tier)

    @property
    def loan_limit(self) -> int:
        return self.LOAN_LIMITS[self.tier]

    def extended(self, until: date) -> Membership:
        if until <= self.valid_until:
            raise MembershipNotExtended(valid_until=self.valid_until, until=until)
        return replace(self, valid_until=until)


@dataclass
class Reader:
    """Корень агрегата."""

    full_name: str
    contact: Contact
    membership: Membership
    is_blocked: bool = False
    id: int | None = None

    def check(self) -> None:
        if not self.full_name.strip():
            raise FullNameEmpty
        self.contact.check()
        self.membership.check()

    def extend_membership(self, until: date) -> None:
        self.membership = self.membership.extended(until)

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
