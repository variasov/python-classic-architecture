from datetime import date
from typing import Any

from classic.scheduler.task import CronTask
from falcon import testing

BOOK: dict[str, Any] = {
    'isbn': '9785171183672',
    'title': 'Анна Каренина',
    'authors': ['Лев Толстой'],
    'published_year': 1877,
}

COPY: dict[str, Any] = {
    'inventory_number': 'INV-E2E-OVERDUE-1',
    'hall': 'Читальный зал',
    'rack': 4,
    'shelf': 2,
}

READER: dict[str, Any] = {
    'full_name': 'Мария Смирнова',
    'email': 'reader-overdue-e2e@example.com',
    'phone': '+7 900 111-22-33',
    'tier': 'premium',
    'valid_until': '2030-12-31',
}


def test_scheduler_registers_daily_overdue_reminder(test_env: None) -> None:
    from library.composites.app.commands.loans.remind_overdue_loans import (
        remind_overdue_loans,
    )
    from library.composites.interfaces.overdue_scheduler.scheduler import (
        scheduler,
    )

    tasks = list(scheduler._inbox.queue)

    assert len(tasks) == 1
    task = tasks[0]
    assert isinstance(task, CronTask)
    assert task._schedule.expressions == ['0', '9', '*', '*', '*']
    assert task._job == remind_overdue_loans.run


def test_scheduler_creates_overdue_notification_once(
    client: testing.TestClient,
    raw_db: Any,
    test_env: None,
) -> None:
    from library.composites.app.commands.loans.remind_overdue_loans import (
        remind_overdue_loans,
    )

    email = READER['email']
    raw_db.execute('DELETE FROM library.readers WHERE email = %(email)s', email=email)
    raw_db.execute(
        'DELETE FROM library.books WHERE isbn = %(isbn)s',
        isbn=BOOK['isbn'],
    )
    book_id: int | None = None
    reader_id: int | None = None
    try:
        book_id, copy_id, reader_id = _create_loan_entities(client)
        issued = client.simulate_post(
            '/library/loans',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'copy_id': copy_id},
        )
        assert issued.status_code == 201
        loan_id: int = issued.json['id']

        raw_db.execute(
            'UPDATE library.loans '
            'SET period_start = current_date - 15, period_due = current_date - 1 '
            'WHERE id = %(loan_id)s',
            loan_id=loan_id,
        )

        assert remind_overdue_loans.run() == 1
        assert raw_db.scalar(
            'SELECT kind FROM library.notifications WHERE loan_id = %(loan_id)s '
            "AND kind = 'loan_overdue'",
            loan_id=loan_id,
        ) == 'loan_overdue'
        assert raw_db.scalar(
            'SELECT reader_id FROM library.notifications WHERE loan_id = %(loan_id)s '
            "AND kind = 'loan_overdue'",
            loan_id=loan_id,
        ) == reader_id
        assert str(
            raw_db.scalar(
                'SELECT created_at FROM library.notifications '
                'WHERE loan_id = %(loan_id)s AND kind = %(kind)s',
                loan_id=loan_id,
                kind='loan_overdue',
            ),
        ) == str(date.today())

        assert remind_overdue_loans.run() == 0
        assert raw_db.scalar(
            'SELECT count(*) FROM library.notifications '
            'WHERE loan_id = %(loan_id)s AND kind = %(kind)s',
            loan_id=loan_id,
            kind='loan_overdue',
        ) == 1
    finally:
        if reader_id is not None:
            raw_db.execute(
                'DELETE FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
        if book_id is not None:
            raw_db.execute(
                'DELETE FROM library.books WHERE id = %(id)s',
                id=book_id,
            )


def _create_loan_entities(client: testing.TestClient) -> tuple[int, int, int]:
    book = client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json=BOOK,
    )
    assert book.status_code == 201
    book_id: int = book.json['id']

    copy = client.simulate_post(
        '/library/copies',
        headers={'X-User': 'admin'},
        json={**COPY, 'book_id': book_id},
    )
    assert copy.status_code == 201
    copy_id: int = copy.json['id']

    reader = client.simulate_post(
        '/library/readers',
        headers={'X-User': 'admin'},
        json=READER,
    )
    assert reader.status_code == 201
    reader_id: int = reader.json['id']
    return book_id, copy_id, reader_id
