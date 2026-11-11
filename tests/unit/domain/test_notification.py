from collections.abc import Callable
from datetime import date

from library.app.commands.domain.notification import (
    Notification,
    NotificationKind,
    NotificationNotFound,
)

TODAY = date(2026, 3, 10)


def test_notification_holds_fields(
    notification_factory: Callable[..., Notification],
) -> None:
    notification = notification_factory(
        reader_id=3,
        loan_id=7,
        kind=NotificationKind.loan_overdue,
    )

    assert notification.reader_id == 3
    assert notification.loan_id == 7
    assert notification.kind is NotificationKind.loan_overdue
    assert notification.created_at == TODAY
    assert notification.id is None


def test_kinds_have_stable_text_values() -> None:
    assert NotificationKind.loan_issued.value == 'loan_issued'
    assert NotificationKind.loan_overdue.value == 'loan_overdue'


def test_valid_notification_passes_check(
    notification_factory: Callable[..., Notification],
) -> None:
    notification_factory().check()


def test_about_loan_on_instance(
    notification_factory: Callable[..., Notification],
) -> None:
    notification = notification_factory(loan_id=5)

    assert notification.about_loan(loan_id=5)
    assert not notification.about_loan(loan_id=6)


def test_about_loan_lazy(
    notification_factory: Callable[..., Notification],
) -> None:
    notification = notification_factory(loan_id=5)
    criteria = Notification.about_loan(loan_id=5)

    assert criteria.is_satisfied_by(notification)
    assert not Notification.about_loan(loan_id=6).is_satisfied_by(notification)


def test_of_kind_on_instance(
    notification_factory: Callable[..., Notification],
) -> None:
    notification = notification_factory(kind=NotificationKind.loan_issued)

    assert notification.of_kind(kind=NotificationKind.loan_issued)
    assert not notification.of_kind(kind=NotificationKind.loan_overdue)


def test_of_kind_lazy(
    notification_factory: Callable[..., Notification],
) -> None:
    notification = notification_factory(kind=NotificationKind.loan_overdue)
    criteria = Notification.of_kind(kind=NotificationKind.loan_overdue)

    assert criteria.is_satisfied_by(notification)
    assert not Notification.of_kind(
        kind=NotificationKind.loan_issued
    ).is_satisfied_by(notification)


def test_criteria_combinations(
    notification_factory: Callable[..., Notification],
) -> None:
    notification = notification_factory(
        loan_id=5, kind=NotificationKind.loan_issued
    )
    matching = (
        Notification.about_loan(loan_id=5)
        & Notification.of_kind(kind=NotificationKind.loan_issued)
    )
    other_loan = Notification.about_loan(loan_id=6) | Notification.of_kind(
        kind=NotificationKind.loan_issued
    )

    assert matching.is_satisfied_by(notification)
    assert other_loan.is_satisfied_by(notification)
    assert not (~Notification.about_loan(loan_id=5)).is_satisfied_by(
        notification
    )


def test_not_found_message() -> None:
    error = NotificationNotFound(id=9)

    assert str(error) == 'Уведомление с id=9 не найдено'
