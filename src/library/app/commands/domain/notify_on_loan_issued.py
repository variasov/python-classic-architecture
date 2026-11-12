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
    ) -> None:
        self._notifications = notifications
        hub.add_reaction(LoanIssued, self._on_loan_issued)

    def _on_loan_issued(self, signal: LoanIssued) -> None:
        notification = Notification(
            reader_id=signal.reader_id,
            loan_id=signal.loan_id,
            kind=NotificationKind.loan_issued,
            created_at=date.today(),
        )
        self._notifications.save(notification)
