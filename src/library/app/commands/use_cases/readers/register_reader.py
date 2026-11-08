import logging
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReadersRepo,
)
from library.app.commands.saved import saved_id
from library.app.roles import Account, PermissionDenied, Permissions


@dataclass(frozen=True)
class RegisterReaderParams:
    full_name: str
    email: str
    valid_until: date
    phone: str | None = None
    tier: str = 'basic'


class RegisterReader:
    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self.readers = readers
        self.logger = logger

    def run(self, account: Account, params: RegisterReaderParams) -> int:
        if not account.can(Permissions.READERS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.READERS_EDIT,
            )
        reader = Reader(
            full_name=params.full_name,
            contact=Contact(email=params.email, phone=params.phone),
            membership=Membership(
                tier=params.tier,
                valid_until=params.valid_until,
            ),
        )
        saved = self.readers.save(reader)
        self.logger.info('Зарегистрирован читатель %r', saved.full_name)
        return saved_id(saved.id)
