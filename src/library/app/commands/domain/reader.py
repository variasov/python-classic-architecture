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
        return f'Email должен содержать @, получено: {self.email}'


@dataclass
class MembershipTierInvalid(DomainError):
    tier: str

    def __str__(self) -> str:
        return f'Неизвестный тариф абонемента: {self.tier}'


@dataclass
class ReaderNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Читатель с id={self.id} не найден'


@dataclass(frozen=True)
class Contact:
    """Объект-значение: контакты читателя"""

    email: str
    phone: str | None = None

    def check(self) -> None:
        if '@' not in self.email:
            raise ContactEmailInvalid(email=self.email)


@dataclass(frozen=True)
class Membership:
    """Объект-значение: абонемент читателя"""

    TIER_LOAN_LIMITS: ClassVar[dict[str, int]] = {'basic': 3, 'premium': 10}

    tier: str
    valid_until: date

    @property
    def loan_limit(self) -> int:
        return self.TIER_LOAN_LIMITS[self.tier]

    def check(self) -> None:
        if self.tier not in self.TIER_LOAN_LIMITS:
            raise MembershipTierInvalid(tier=self.tier)


@dataclass
class Reader:
    """Корень агрегата: читатель"""

    full_name: str
    contact: Contact
    membership: Membership
    is_blocked: bool = False
    id: int | None = None

    def check(self) -> None:
        if not self.full_name.strip():
            raise ReaderNameEmpty()
        self.contact.check()
        self.membership.check()

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
