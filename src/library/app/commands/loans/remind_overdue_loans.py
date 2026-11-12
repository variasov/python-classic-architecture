import logging
from datetime import date

from library.app.domain.loan import Loan, LoansRepo
from library.app.domain.notification import (
    Notification,
    NotificationKind,
    NotificationsRepo,
)


class RemindOverdueLoans:
    """Фоновая команда: напоминает читателям о просроченных выдачах."""

    def __init__(
        self,
        loans: LoansRepo,
        notifications: NotificationsRepo,
        logger: logging.Logger,
    ) -> None:
        self._loans = loans
        self._notifications = notifications
        self._logger = logger

    def run(self) -> int:
        on = date.today()
        overdue_loans = self._loans.find(Loan.overdue(on=on))
        created = 0
        for loan in overdue_loans:
            assert loan.id is not None
            already_notified = self._notifications.find(
                Notification.about_loan(loan_id=loan.id)
                & Notification.of_kind(kind=NotificationKind.loan_overdue),
            )
            if already_notified:
                continue
            saved = self._notifications.save(
                Notification(
                    reader_id=loan.reader_id,
                    loan_id=loan.id,
                    kind=NotificationKind.loan_overdue,
                    created_at=on,
                ),
            )
            created += 1
            self._logger.info(
                'Напоминание о просрочке сохранено: id=%s, loan_id=%s, '
                'reader_id=%s',
                saved.id,
                saved.loan_id,
                saved.reader_id,
            )
        self._logger.info('Напоминаний о просрочке создано: %s', created)
        return created
