import logging
from dataclasses import dataclass
from datetime import date

from classic.signals import Hub

from library.app.commands.signals import LoanIssued
from library.app.domain.borrow_copy import BorrowCopy
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class IssueLoanParams:
    """Параметры выдачи экземпляра читателю."""

    reader_id: int
    copy_id: int


@dataclass(frozen=True)
class LoanCreated:
    """Контракт ответа на выдачу экземпляра."""

    id: int


class IssueLoan:
    """Выдача экземпляра читателю."""

    def __init__(
        self,
        borrow_copy: BorrowCopy,
        hub: Hub,
        logger: logging.Logger,
    ) -> None:
        self._borrow_copy = borrow_copy
        self._hub = hub
        self._logger = logger

    def run(self, params: IssueLoanParams, account: Account) -> LoanCreated:
        account.require(Permissions.LOANS_EDIT)
        loan = self._borrow_copy.run(
            reader_id=params.reader_id,
            copy_id=params.copy_id,
            on=date.today(),
        )
        assert loan.id is not None
        self._hub.notify(LoanIssued(loan_id=loan.id, reader_id=loan.reader_id))
        self._logger.info(
            'Выдача оформлена: id=%s, reader_id=%s, copy_id=%s',
            loan.id,
            loan.reader_id,
            loan.copy_id,
        )
        return LoanCreated(id=loan.id)
