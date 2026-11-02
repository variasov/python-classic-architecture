import logging
from dataclasses import dataclass

from library.app.commands.domain.reader import ReadersRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class BlockReaderParams:
    reader_id: int


class BlockReader:
    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self.readers = readers
        self.logger = logger

    def run(self, params: BlockReaderParams, account: Account) -> None:
        account.ensure(Permissions.READERS_EDIT)
        reader = self.readers.get_by_id(params.reader_id)
        reader.block()
        self.readers.save(reader)
        self.logger.info('Заблокирован читатель %s', params.reader_id)
