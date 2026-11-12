from collections.abc import Callable, Iterator
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

import pytest
from classic.criteria import Criteria, ReturnsTrue

from library.app.domain.book import Book
from library.app.domain.copy import Copy
from library.app.domain.loan import Loan, LoanPeriod
from library.app.domain.notification import (
    Notification,
    NotificationKind,
    NotificationNotFound,
    NotificationsRepo,
)
from library.app.domain.reader import Reader
from library.infra.db.repos.books import DbBooksRepo
from library.infra.db.repos.copies import DbCopiesRepo
from library.infra.db.repos.loans import DbLoansRepo
from library.infra.db.repos.notifications import DbNotificationsRepo
from library.infra.db.repos.readers import DbReadersRepo

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)


@pytest.fixture(params=['db', 'in_memory'])
def notifications_env(
    request: pytest.FixtureRequest,
    db_engine: Any,
    raw_db: Any,
    reader_factory: Callable[..., Reader],
    book_factory: Callable[..., Book],
    copy_factory: Callable[..., Copy],
    loan_factory: Callable[..., Loan],
) -> Iterator[tuple[NotificationsRepo, int, tuple[int, int]]]:
    """Репозиторий уведомлений, id читателя и id двух выдач"""
    if request.param == 'db':
        readers = DbReadersRepo(db_engine)
        books = DbBooksRepo(db_engine)
        copies = DbCopiesRepo(db_engine)
        loans = DbLoansRepo(db_engine)
        reader = readers.save(reader_factory())
        book = books.save(book_factory())
        assert reader.id is not None
        assert book.id is not None
        copy = copies.save(
            copy_factory(book_id=book.id, inventory_number=f'INV-{uuid4().hex}'),
        )
        assert copy.id is not None
        period = LoanPeriod(
            start=TODAY,
            due=TODAY + timedelta(days=Loan.TERM_DAYS),
        )
        loan = loans.save(
            loan_factory(reader_id=reader.id, copy_id=copy.id, period=period),
        )
        other_loan = loans.save(
            loan_factory(reader_id=reader.id, copy_id=copy.id, period=period),
        )
        assert loan.id is not None
        assert other_loan.id is not None
        yield (
            DbNotificationsRepo(db_engine),
            reader.id,
            (loan.id, other_loan.id),
        )
        raw_db.execute(
            'DELETE FROM library.readers WHERE id = %(id)s',
            id=reader.id,
        )
        raw_db.execute(
            'DELETE FROM library.books WHERE id = %(id)s',
            id=book.id,
        )
        return
    in_memory: NotificationsRepo = request.getfixturevalue(
        'in_memory_notifications_repo',
    )
    yield in_memory, 1, (1, 2)


def _load(repo: NotificationsRepo, notification: Notification) -> Notification:
    assert notification.id is not None
    return repo.get_by_id(notification.id)


def test_saved_notification_is_read_back(
    notifications_env: tuple[NotificationsRepo, int, tuple[int, int]],
    notification_factory: Callable[..., Notification],
) -> None:
    repo, reader_id, (loan_id, _) = notifications_env
    notification = repo.save(
        notification_factory(
            reader_id=reader_id,
            loan_id=loan_id,
            kind=NotificationKind.loan_issued,
        ),
    )

    loaded = _load(repo, notification)

    assert loaded == notification
    assert loaded.kind is NotificationKind.loan_issued
    assert loaded.created_at == TODAY


def test_update_changes_kind_and_date(
    notifications_env: tuple[NotificationsRepo, int, tuple[int, int]],
    notification_factory: Callable[..., Notification],
) -> None:
    repo, reader_id, (loan_id, _) = notifications_env
    notification = repo.save(
        notification_factory(reader_id=reader_id, loan_id=loan_id),
    )
    notification.kind = NotificationKind.loan_overdue
    notification.created_at = TOMORROW

    repo.save(notification)
    loaded = _load(repo, notification)

    assert loaded.kind is NotificationKind.loan_overdue
    assert loaded.created_at == TOMORROW


def test_get_missing_notification_raises(
    notifications_env: tuple[NotificationsRepo, int, tuple[int, int]],
) -> None:
    repo, _, _ = notifications_env

    with pytest.raises(NotificationNotFound):
        repo.get_by_id(987654)


@pytest.fixture
def seeded_notifications(
    notifications_env: tuple[NotificationsRepo, int, tuple[int, int]],
    notification_factory: Callable[..., Notification],
) -> list[Notification]:
    repo, reader_id, (loan_id, other_loan_id) = notifications_env
    return [
        repo.save(
            notification_factory(
                reader_id=reader_id,
                loan_id=loan_id,
                kind=NotificationKind.loan_issued,
            ),
        ),
        repo.save(
            notification_factory(
                reader_id=reader_id,
                loan_id=loan_id,
                kind=NotificationKind.loan_overdue,
                created_at=TOMORROW,
            ),
        ),
        repo.save(
            notification_factory(
                reader_id=reader_id,
                loan_id=other_loan_id,
                kind=NotificationKind.loan_issued,
            ),
        ),
        repo.save(
            notification_factory(
                reader_id=reader_id,
                loan_id=other_loan_id,
                kind=NotificationKind.loan_overdue,
                created_at=TOMORROW,
            ),
        ),
    ]


def _criteria_map(
    loan_id: int,
    other_loan_id: int,
) -> dict[str, Criteria[Notification]]:
    return {
        'about_loan': Notification.about_loan(loan_id=loan_id),
        'other_loan': Notification.about_loan(loan_id=other_loan_id),
        'of_kind': Notification.of_kind(kind=NotificationKind.loan_issued),
        'about_loan_and_of_kind': Notification.about_loan(loan_id=loan_id)
        & Notification.of_kind(kind=NotificationKind.loan_overdue),
        'about_loan_or_of_kind': Notification.about_loan(loan_id=loan_id)
        | Notification.of_kind(kind=NotificationKind.loan_issued),
        'not_about_loan': ~Notification.about_loan(loan_id=loan_id),
    }


@pytest.mark.parametrize(
    'criteria_name',
    [
        'about_loan',
        'other_loan',
        'of_kind',
        'about_loan_and_of_kind',
        'about_loan_or_of_kind',
        'not_about_loan',
    ],
)
def test_criteria_sql_matches_domain(
    notifications_env: tuple[NotificationsRepo, int, tuple[int, int]],
    seeded_notifications: list[Notification],
    criteria_name: str,
) -> None:
    repo, _, (loan_id, other_loan_id) = notifications_env
    criteria = _criteria_map(loan_id, other_loan_id)[criteria_name]

    found = repo.find(criteria)
    expected = [
        notification
        for notification in seeded_notifications
        if criteria.is_satisfied_by(notification)
    ]

    assert [item.id for item in found] == [item.id for item in expected]


def test_find_returns_all_without_filters(
    notifications_env: tuple[NotificationsRepo, int, tuple[int, int]],
    seeded_notifications: list[Notification],
) -> None:
    repo, _, _ = notifications_env

    assert len(repo.find(ReturnsTrue())) == len(seeded_notifications)
