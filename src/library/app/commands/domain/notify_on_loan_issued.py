import logging
from datetime import date

from classic.signals import Hub

from library.app.commands.domain.events import LoanIssued
from library.app.commands.domain.notification import (
    Notification,
    NotificationKind,
    NotificationsRepo,
)


class NotifyOnLoanIssued:
    """Реакция на выдачу: сохраняет уведомление читателю."""

    def __init__(
        self,
        hub: Hub,
        notifications: NotificationsRepo,
        logger: logging.Logger,
    ) -> None:
        self._notifications = notifications
        self._logger = logger
        hub.add_reaction(LoanIssued, self._on_loan_issued)

    def _on_loan_issued(self, signal: LoanIssued) -> None:
        notification = Notification(
            reader_id=signal.reader_id,
            loan_id=signal.loan_id,
            kind=NotificationKind.loan_issued,
            created_at=date.today(),
        )
        saved = self._notifications.save(notification)
        self._logger.info(
            'Уведомление о выдаче сохранено: id=%s, loan_id=%s, reader_id=%s',
            saved.id,
            saved.loan_id,
            saved.reader_id,
        )
