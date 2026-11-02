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
    full_name: str
    email: str
    tier: str
    valid_until: date
    phone: str | None = None


class RegisterReader:
    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self.readers = readers
        self.logger = logger

    def run(self, params: RegisterReaderParams, account: Account) -> int:
        account.ensure(Permissions.READERS_EDIT)
        reader = Reader(
            full_name=params.full_name,
            contact=Contact(email=params.email, phone=params.phone),
            membership=Membership(tier=params.tier, valid_until=params.valid_until),
        )
        reader = self.readers.save(reader)
        self.logger.info('Зарегистрирован читатель %s', reader.id)
        assert reader.id is not None  # noqa: S101 - save выдаёт id
        return reader.id
