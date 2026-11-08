import logging
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.reader import ReadersRepo
from library.app.roles import Account, PermissionDenied, Permissions


@dataclass(frozen=True)
class ExtendMembershipParams:
    reader_id: int
    until: date


class ExtendMembership:
    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self.readers = readers
        self.logger = logger

    def run(self, account: Account, params: ExtendMembershipParams) -> None:
        if not account.can(Permissions.READERS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.READERS_EDIT,
            )
        reader = self.readers.get_by_id(params.reader_id)
        reader.extend_membership(until=params.until)
        self.readers.save(reader)
        self.logger.info(
            'Продлено членство читателя с id=%s',
            params.reader_id,
        )
