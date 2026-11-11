import logging
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReadersRepo,
)
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class RegisterReaderParams:
    """Параметры регистрации читателя"""

    full_name: str
    email: str
    phone: str | None
    tier: str
    valid_until: date


class RegisterReader:
    """Регистрация читателя"""

    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self._readers = readers
        self._logger = logger

    def run(self, params: RegisterReaderParams, account: Account) -> int:
        account.require(Permissions.READERS_EDIT)
        reader = Reader(
            full_name=params.full_name,
            contact=Contact(email=params.email, phone=params.phone),
            membership=Membership(tier=params.tier, valid_until=params.valid_until),
        )
        saved = self._readers.save(reader)
        assert saved.id is not None
        self._logger.info('Читатель зарегистрирован: id=%s', saved.id)
        return saved.id
