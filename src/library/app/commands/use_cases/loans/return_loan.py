import logging
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.return_copy import ReturnCopy
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class ReturnLoanParams:
    """Параметры возврата экземпляра"""

    loan_id: int


class ReturnLoan:
    """Возврат экземпляра по выдаче"""

    def __init__(self, return_copy: ReturnCopy, logger: logging.Logger) -> None:
        self._return_copy = return_copy
        self._logger = logger

    def run(self, params: ReturnLoanParams, account: Account) -> None:
        account.require(Permissions.LOANS_EDIT)
        self._return_copy.run(params.loan_id, on=date.today())
        self._logger.info('Экземпляр возвращён: loan_id=%s', params.loan_id)
