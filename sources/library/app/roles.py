from dataclasses import dataclass

from library.app.errors import AppError


class Permissions:
    BOOKS_EDIT = 'books.edit'
    READERS_EDIT = 'readers.edit'
    LOANS_EDIT = 'loans.edit'


@dataclass
class PermissionDenied(AppError):
    login: str
    permission: str

    def __str__(self) -> str:
        return f'У пользователя {self.login} нет права {self.permission}'


@dataclass(frozen=True)
class Account:
    login: str
    permissions: frozenset[str]

    def ensure(self, permission: str) -> None:
        if permission not in self.permissions:
            raise PermissionDenied(login=self.login, permission=permission)
