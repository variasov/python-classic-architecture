import logging
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.return_loan import ReturnLoan
from library.app.roles import Account, PermissionDenied, Permissions


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

    def run(self, account: Account, params: ReturnLoanCommandParams) -> None:
        if not account.can(Permissions.LOANS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.LOANS_EDIT,
            )
        self.return_loan.run(
            loan_id=params.loan_id,
            on=self.clock.today(),
        )
        self.logger.info('Возвращена выдача с id=%s', params.loan_id)
