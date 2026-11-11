import logging
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.reader import ReadersRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class ExtendMembershipParams:
    """Параметры продления абонемента"""

    reader_id: int
    valid_until: date


class ExtendMembership:
    """Продление абонемента читателя"""

    def __init__(self, readers: ReadersRepo, logger: logging.Logger) -> None:
        self._readers = readers
        self._logger = logger

    def run(self, params: ExtendMembershipParams, account: Account) -> None:
        account.require(Permissions.READERS_EDIT)
        reader = self._readers.get_by_id(params.reader_id)
        reader.extend_membership(until=params.valid_until)
        self._readers.save(reader)
        self._logger.info(
            'Абонемент продлён: reader_id=%s, valid_until=%s',
            params.reader_id,
            params.valid_until,
        )
