import logging
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from library.app.domain.loan import LoansRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class ExtendLoanParams:
    """Параметры продления выдачи."""

    MAX_DAYS: ClassVar[int] = 30

    loan_id: int
    days: int

    def __post_init__(self) -> None:
        if not 0 < self.days <= self.MAX_DAYS:
            raise ValueError(f'days должен быть от 1 до {self.MAX_DAYS}')


class ExtendLoan:
    """Продление выдачи."""

    def __init__(self, loans: LoansRepo, logger: logging.Logger) -> None:
        self._loans = loans
        self._logger = logger

    def run(self, params: ExtendLoanParams, account: Account) -> None:
        account.require(Permissions.LOANS_EDIT)
        loan = self._loans.get_by_id(params.loan_id)
        loan.extend(days=params.days, on=date.today())
        self._loans.save(loan)
        self._logger.info(
            'Выдача продлена: loan_id=%s, days=%s, due=%s',
            params.loan_id,
            params.days,
            loan.period.due,
        )
