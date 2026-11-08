from datetime import datetime, time, timedelta, timezone


def test_overdue_scheduler_request_creates_notifications(
    api_client,
    raw_db,
    create_book,
    create_reader,
    add_copy,
    issue_loan,
    monkeypatch,
) -> None:
    # Импорт композита требует переменных окружения из test_env.
    from library.composites.infra.clock.system import clock  # noqa: PLC0415
    from library.composites.interfaces.overdue_scheduler.jobs import (  # noqa: PLC0415
        request_overdue_reminders,
    )

    book_id = create_book()
    add_copy(book_id)
    reader_id = create_reader()

    past = datetime.combine(
        datetime.now(tz=timezone.utc).date() - timedelta(days=60),
        time(12),
        tzinfo=timezone.utc,
    )
    monkeypatch.setattr(clock, 'now', lambda: past)
    loan_id = issue_loan(reader_id, book_id)
    monkeypatch.undo()

    before = raw_db.scalar(
        'SELECT count(*) FROM library.notifications',
    )
    request_overdue_reminders()
    after = raw_db.scalar(
        'SELECT count(*) FROM library.notifications',
    )
    assert after == before + 1

    message = raw_db.scalar(
        'SELECT message FROM library.notifications ORDER BY id DESC LIMIT 1',
    )
    assert f'id={loan_id}' in message
