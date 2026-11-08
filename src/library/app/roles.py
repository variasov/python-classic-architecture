from dataclasses import dataclass

from library.app.commands.domain.errors import DomainError


class Permissions:
    BOOKS_EDIT = 'books.edit'
    READERS_EDIT = 'readers.edit'
    LOANS_EDIT = 'loans.edit'


@dataclass(frozen=True)
class Account:
    login: str
    permissions: frozenset[str]

    def can(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass
class PermissionDenied(DomainError):
    login: str
    permission: str

    def __str__(self) -> str:
        return f'Пользователю {self.login!r} запрещено действие {self.permission!r}'
