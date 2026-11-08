import logging
from dataclasses import dataclass

from classic.signals import Hub

from library.app.clock import Clock
from library.app.commands.domain.issue_loan import IssueLoan
from library.app.commands.saved import saved_id
from library.app.commands.signals import LoanIssued
from library.app.roles import Account, PermissionDenied, Permissions


@dataclass(frozen=True)
class IssueLoanCommandParams:
    reader_id: int
    book_id: int
    inventory_number: str


class IssueLoanCommand:
    def __init__(
        self,
        issue_loan: IssueLoan,
        clock: Clock,
        hub: Hub,
        logger: logging.Logger,
    ) -> None:
        self.issue_loan = issue_loan
        self.clock = clock
        self.hub = hub
        self.logger = logger

    def run(self, account: Account, params: IssueLoanCommandParams) -> int:
        if not account.can(Permissions.LOANS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.LOANS_EDIT,
            )
        loan = self.issue_loan.run(
            reader_id=params.reader_id,
            book_id=params.book_id,
            inventory_number=params.inventory_number,
            on=self.clock.today(),
        )
        loan_id = saved_id(loan.id)
        self.hub.notify(
            LoanIssued(loan_id=loan_id, reader_id=params.reader_id),
        )
        self.logger.info('Выдана книга, выдача id=%s', loan_id)
        return loan_id
