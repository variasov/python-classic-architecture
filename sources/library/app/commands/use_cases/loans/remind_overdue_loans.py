import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from library.app.commands.domain.loan import Loan, LoansRepo


class NotificationsOutbox(ABC):
    """Очередь исходящих уведомлений."""

    @abstractmethod
    def put(self, kind: str, reader_id: int, loan_id: int, text: str) -> None: ...


@dataclass(frozen=True)
class RemindOverdueLoansParams:
    on: date


class RemindOverdueLoans:
    """Фоновая команда: работает без пользователя."""

    def __init__(
        self,
        loans: LoansRepo,
        outbox: NotificationsOutbox,
        logger: logging.Logger,
    ) -> None:
        self.loans = loans
        self.outbox = outbox
        self.logger = logger

    def run(self, params: RemindOverdueLoansParams) -> int:
        overdue = self.loans.find(Loan.overdue(on=params.on))
        for loan in overdue:
            assert loan.id is not None  # noqa: S101 - найденная выдача сохранена
            self.outbox.put(
                kind='overdue_reminder',
                reader_id=loan.reader_id,
                loan_id=loan.id,
                text=f'Выдача {loan.id} просрочена, срок был {loan.period.due}',
            )
        self.logger.info('Напоминаний о просрочке: %s', len(overdue))
        return len(overdue)
