import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.loan import Loan, LoansRepo


class NotificationsGateway(ABC):
    @abstractmethod
    def add(self, message: str) -> None: ...


@dataclass(frozen=True)
class RemindOverdueLoansParams:
    on: date


class RemindOverdueLoans:
    def __init__(
        self,
        loans: LoansRepo,
        notifications: NotificationsGateway,
        logger: logging.Logger,
    ) -> None:
        self.loans = loans
        self.notifications = notifications
        self.logger = logger

    def run(self, params: RemindOverdueLoansParams) -> int:
        overdue: list[Loan] = self.loans.find(Loan.overdue(on=params.on))
        for loan in overdue:
            self.notifications.add(
                f'Просрочена выдача с id={loan.id} (читатель {loan.reader_id})',
            )
        self.logger.info(
            'Создано напоминаний о просроченных выдачах: %s',
            len(overdue),
        )
        return len(overdue)
