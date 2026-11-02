import logging
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.reader import ReadersRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class ExtendMembershipParams:
    reader_id: int
    until: date


class ExtendMembership:
    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self.readers = readers
        self.logger = logger

    def run(self, params: ExtendMembershipParams, account: Account) -> None:
        account.ensure(Permissions.READERS_EDIT)
        reader = self.readers.get_by_id(params.reader_id)
        reader.extend_membership(params.until)
        self.readers.save(reader)
        self.logger.info('Продлено членство читателя %s', params.reader_id)
