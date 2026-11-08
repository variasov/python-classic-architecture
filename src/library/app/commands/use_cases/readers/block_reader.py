import logging
from dataclasses import dataclass

from library.app.commands.domain.reader import ReadersRepo
from library.app.roles import Account, PermissionDenied, Permissions


@dataclass(frozen=True)
class BlockReaderParams:
    reader_id: int


class BlockReader:
    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self.readers = readers
        self.logger = logger

    def run(self, account: Account, params: BlockReaderParams) -> None:
        if not account.can(Permissions.READERS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.READERS_EDIT,
            )
        reader = self.readers.get_by_id(params.reader_id)
        reader.block()
        self.readers.save(reader)
        self.logger.info('Заблокирован читатель с id=%s', params.reader_id)
