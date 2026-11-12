import logging
from dataclasses import dataclass

from library.app.domain.reader import ReadersRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class UnblockReaderParams:
    """Параметры разблокировки читателя."""

    reader_id: int


class UnblockReader:
    """Разблокировка читателя."""

    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self._readers = readers
        self._logger = logger

    def run(self, params: UnblockReaderParams, account: Account) -> None:
        account.require(Permissions.READERS_EDIT)
        reader = self._readers.get_by_id(params.reader_id)
        reader.unblock()
        self._readers.save(reader)
        self._logger.info(
            'Читатель разблокирован: reader_id=%s',
            params.reader_id,
        )
