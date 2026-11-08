import logging
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.loan import LoansRepo
from library.app.roles import Account, PermissionDenied, Permissions


@dataclass(frozen=True)
class ExtendLoanParams:
    loan_id: int
    days: int


class ExtendLoan:
    def __init__(
        self,
        loans: LoansRepo,
        clock: Clock,
        logger: logging.Logger,
    ) -> None:
        self.loans = loans
        self.clock = clock
        self.logger = logger

    def run(self, account: Account, params: ExtendLoanParams) -> None:
        if not account.can(Permissions.LOANS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.LOANS_EDIT,
            )
        loan = self.loans.get_by_id(params.loan_id)
        loan.extend(on=self.clock.today(), days=params.days)
        self.loans.save(loan)
        self.logger.info('Продлена выдача с id=%s', params.loan_id)
