import logging
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.return_loan import ReturnLoan
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class ReturnLoanCommandParams:
    loan_id: int


class ReturnLoanCommand:
    def __init__(
        self,
        return_loan: ReturnLoan,
        clock: Clock,
        logger: logging.Logger,
    ) -> None:
        self.return_loan = return_loan
        self.clock = clock
        self.logger = logger

    def run(self, params: ReturnLoanCommandParams, account: Account) -> None:
        account.ensure(Permissions.LOANS_EDIT)
        self.return_loan.run(loan_id=params.loan_id, on=self.clock.today())
        self.logger.info('Возвращена выдача %s', params.loan_id)
