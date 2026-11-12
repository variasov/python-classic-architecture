import logging
from collections.abc import Callable
from datetime import date, timedelta

import pytest
from classic.criteria import ReturnsTrue

from library.app.commands.loans.remind_overdue_loans import (
    RemindOverdueLoans,
)
from library.app.domain.loan import Loan, LoanPeriod, LoansRepo
from library.app.domain.notification import (
    Notification,
    NotificationKind,
    NotificationsRepo,
)

TODAY = date.today()
OVERDUE_PERIOD = LoanPeriod(
    start=TODAY - timedelta(days=Loan.TERM_DAYS),
    due=TODAY - timedelta(days=1),
)
ACTIVE_PERIOD = LoanPeriod(
    start=TODAY,
    due=TODAY + timedelta(days=Loan.TERM_DAYS),
)


def _id(loan: Loan) -> int:
    assert loan.id is not None
    return loan.id


@pytest.fixture
def loans_repo(in_memory_loans_repo: LoansRepo) -> LoansRepo:
    return in_memory_loans_repo


@pytest.fixture
def notifications_repo(
    in_memory_notifications_repo: NotificationsRepo,
) -> NotificationsRepo:
    return in_memory_notifications_repo


@pytest.fixture
def remind_overdue_loans(
    loans_repo: LoansRepo,
    notifications_repo: NotificationsRepo,
) -> RemindOverdueLoans:
    return RemindOverdueLoans(
        loans=loans_repo,
        notifications=notifications_repo,
        logger=logging.getLogger('test'),
    )


def test_creates_notifications_only_for_overdue_loans(
    remind_overdue_loans: RemindOverdueLoans,
    loans_repo: LoansRepo,
    notifications_repo: NotificationsRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    overdue = loans_repo.save(
        loan_factory(reader_id=1, copy_id=1, period=OVERDUE_PERIOD),
    )
    loans_repo.save(loan_factory(reader_id=2, copy_id=2, period=ACTIVE_PERIOD))
    loans_repo.save(
        loan_factory(
            reader_id=3,
            copy_id=3,
            period=LoanPeriod(
                start=TODAY - timedelta(days=30),
                due=TODAY - timedelta(days=5),
            ),
            returned_at=TODAY - timedelta(days=6),
        ),
    )

    created = remind_overdue_loans.run()

    assert created == 1
    notifications = notifications_repo.find(ReturnsTrue())
    assert len(notifications) == 1
    notification = notifications[0]
    assert notification.reader_id == overdue.reader_id
    assert notification.loan_id == overdue.id
    assert notification.kind is NotificationKind.loan_overdue
    assert notification.created_at == TODAY


def test_repeated_run_does_not_duplicate_notifications(
    remind_overdue_loans: RemindOverdueLoans,
    loans_repo: LoansRepo,
    notifications_repo: NotificationsRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loans_repo.save(loan_factory(period=OVERDUE_PERIOD))
    loan_id = _id(loan)

    assert remind_overdue_loans.run() == 1
    assert remind_overdue_loans.run() == 0

    notifications = notifications_repo.find(
        Notification.about_loan(loan_id=loan_id)
        & Notification.of_kind(kind=NotificationKind.loan_overdue),
    )
    assert len(notifications) == 1


def test_loan_issued_notification_does_not_skip_overdue_reminder(
    remind_overdue_loans: RemindOverdueLoans,
    loans_repo: LoansRepo,
    notifications_repo: NotificationsRepo,
    notification_factory: Callable[..., Notification],
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loans_repo.save(loan_factory(period=OVERDUE_PERIOD))
    loan_id = _id(loan)
    notifications_repo.save(
        notification_factory(
            reader_id=loan.reader_id,
            loan_id=loan_id,
            kind=NotificationKind.loan_issued,
        ),
    )

    created = remind_overdue_loans.run()

    assert created == 1
    kinds = {
        notification.kind
        for notification in notifications_repo.find(
            Notification.about_loan(loan_id=loan_id),
        )
    }
    assert kinds == {NotificationKind.loan_issued, NotificationKind.loan_overdue}


def test_returns_number_of_new_notifications(
    remind_overdue_loans: RemindOverdueLoans,
    loans_repo: LoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    for copy_id in range(1, 4):
        loans_repo.save(
            loan_factory(
                reader_id=copy_id,
                copy_id=copy_id,
                period=OVERDUE_PERIOD,
            ),
        )

    assert remind_overdue_loans.run() == 3


def test_returns_zero_without_overdue_loans(
    remind_overdue_loans: RemindOverdueLoans,
    loans_repo: LoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loans_repo.save(loan_factory(period=ACTIVE_PERIOD))

    assert remind_overdue_loans.run() == 0
