import logging
from dataclasses import dataclass
from typing import ClassVar

from classic.signals import Hub
from library.app.clock import Clock
from library.app.commands.domain.issue_loan import IssueLoan
from library.app.commands.signals import LoanIssued
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class IssueLoanCommandParams:
    MAX_DAYS: ClassVar[int] = 60

    reader_id: int
    book_id: int
    inventory_number: str
    days: int = 14

    def __post_init__(self) -> None:
        if not 0 < self.days <= self.MAX_DAYS:
            raise ValueError(f'days должен быть от 1 до {self.MAX_DAYS}')


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

    def run(self, params: IssueLoanCommandParams, account: Account) -> int:
        account.ensure(Permissions.LOANS_EDIT)
        today = self.clock.today()
        loan = self.issue_loan.run(
            reader_id=params.reader_id,
            book_id=params.book_id,
            inventory_number=params.inventory_number,
            on=today,
            days=params.days,
        )
        assert loan.id is not None  # noqa: S101 - save выдаёт id
        self.hub.notify(LoanIssued(loan_id=loan.id, reader_id=params.reader_id))
        self.logger.info('Выдача %s читателю %s', loan.id, params.reader_id)
        return loan.id
