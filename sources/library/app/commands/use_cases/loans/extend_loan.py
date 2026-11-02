import logging
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.loan import LoansRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class ExtendLoanParams:
    loan_id: int
    days: int

    def __post_init__(self) -> None:
        if self.days <= 0:
            raise ValueError('days должен быть положительным')


class ExtendLoan:
    def __init__(self, loans: LoansRepo, clock: Clock, logger: logging.Logger) -> None:
        self.loans = loans
        self.clock = clock
        self.logger = logger

    def run(self, params: ExtendLoanParams, account: Account) -> None:
        account.ensure(Permissions.LOANS_EDIT)
        today = self.clock.today()
        loan = self.loans.get_by_id(params.loan_id)
        loan.extend(today, params.days)
        self.loans.save(loan)
        self.logger.info('Продлена выдача %s', params.loan_id)
