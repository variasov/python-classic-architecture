import logging
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.borrow_copy import BorrowCopy
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class IssueLoanParams:
    """Параметры выдачи экземпляра читателю"""

    reader_id: int
    copy_id: int


class IssueLoan:
    """Выдача экземпляра читателю"""

    def __init__(self, borrow_copy: BorrowCopy, logger: logging.Logger) -> None:
        self._borrow_copy = borrow_copy
        self._logger = logger

    def run(self, params: IssueLoanParams, account: Account) -> int:
        account.require(Permissions.LOANS_EDIT)
        loan = self._borrow_copy.run(
            reader_id=params.reader_id,
            copy_id=params.copy_id,
            on=date.today(),
        )
        assert loan.id is not None
        self._logger.info(
            'Выдача оформлена: id=%s, reader_id=%s, copy_id=%s',
            loan.id,
            loan.reader_id,
            loan.copy_id,
        )
        return loan.id
