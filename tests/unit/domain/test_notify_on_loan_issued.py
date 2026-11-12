from datetime import date

import pytest
from classic.criteria import ReturnsTrue
from classic.signals import Hub

from library.app.commands.domain.events import LoanIssued
from library.app.commands.domain.notification import (
    NotificationKind,
    NotificationsRepo,
)
from library.app.commands.domain.notify_on_loan_issued import NotifyOnLoanIssued


@pytest.fixture
def hub() -> Hub:
    return Hub()


@pytest.fixture
def notifications_repo(
    in_memory_notifications_repo: NotificationsRepo,
) -> NotificationsRepo:
    return in_memory_notifications_repo


@pytest.fixture
def reaction(
    hub: Hub,
    notifications_repo: NotificationsRepo,
) -> NotifyOnLoanIssued:
    return NotifyOnLoanIssued(
        hub=hub,
        notifications=notifications_repo,
    )


def test_loan_issued_saves_notification(
    reaction: NotifyOnLoanIssued,
    hub: Hub,
    notifications_repo: NotificationsRepo,
) -> None:
    hub.notify(LoanIssued(loan_id=7, reader_id=3))

    notifications = notifications_repo.find(ReturnsTrue())

    assert len(notifications) == 1
    notification = notifications[0]
    assert notification.reader_id == 3
    assert notification.loan_id == 7
    assert notification.kind is NotificationKind.loan_issued
    assert notification.created_at == date.today()
    assert notification.id is not None


def test_each_loan_issued_gets_own_notification(
    reaction: NotifyOnLoanIssued,
    hub: Hub,
    notifications_repo: NotificationsRepo,
) -> None:
    hub.notify(
        LoanIssued(loan_id=7, reader_id=3),
        LoanIssued(loan_id=8, reader_id=4),
    )

    notifications = notifications_repo.find(ReturnsTrue())

    assert [(item.loan_id, item.reader_id) for item in notifications] == [
        (7, 3),
        (8, 4),
    ]
