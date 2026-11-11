from dataclasses import dataclass
from typing import ClassVar, Collection

from library.app.errors import AuthError


class Permissions:
    """Права, которые проверяют usecase-команды"""

    BOOKS_EDIT: ClassVar[str] = 'books.edit'
    READERS_EDIT: ClassVar[str] = 'readers.edit'
    LOANS_EDIT: ClassVar[str] = 'loans.edit'


@dataclass(frozen=True)
class Account:
    """Пользователь, от имени которого выполняется действие"""

    login: str
    permissions: Collection[str]

    def require(self, permission: str) -> None:
        if permission not in self.permissions:
            raise PermissionDenied(login=self.login, permission=permission)


@dataclass
class PermissionDenied(AuthError):
    login: str
    permission: str

    def __str__(self) -> str:
        return f'Пользователю {self.login} запрещено: {self.permission}'
