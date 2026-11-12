from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from library.app.roles import Permissions

DEFAULT_USERS: Final[dict[str, list[str]]] = {
    'admin': [
        Permissions.BOOKS_EDIT,
        Permissions.READERS_EDIT,
        Permissions.LOANS_EDIT,
    ],
    'librarian': [
        Permissions.BOOKS_EDIT,
        Permissions.READERS_EDIT,
        Permissions.LOANS_EDIT,
    ],
    'cataloger': [Permissions.BOOKS_EDIT],
}


class ApiSettings(BaseSettings):
    """Настройки HTTP API и демо-таблицы пользователей."""

    API_HOST: str
    API_PORT: int
    USERS: dict[str, list[str]] = Field(default_factory=lambda: dict(DEFAULT_USERS))

    model_config = SettingsConfigDict(extra='ignore')
