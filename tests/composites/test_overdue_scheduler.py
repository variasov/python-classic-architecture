from collections.abc import Callable
from datetime import timedelta
from types import ModuleType

import pytest
from library.app.commands.domain.loan import Loan, LoanPeriod

from tests.conftest import RawDb


@pytest.fixture(scope='session')
def scheduler_jobs(test_env: None) -> ModuleType:
    from library.composites.interfaces.overdue_scheduler import jobs  # noqa: PLC0415

    return jobs


def test_job_creates_reminders_for_overdue_loans(
    scheduler_jobs: ModuleType,
    create_book: Callable[..., int],
    register_reader: Callable[..., int],
    raw_db: RawDb,
) -> None:
    from library.composites.infra.clock.system import clock  # noqa: PLC0415
    from library.composites.infra.db.repos.loans_repo import loans_repo  # noqa: PLC0415

    book_id, reader_id = create_book(), register_reader()
    today = clock.today()
    start = today - timedelta(days=30)
    overdue = loans_repo.save(
        Loan(
            reader_id=reader_id,
            book_id=book_id,
            inventory_number='INV-0',
            issued_at=start,
            period=LoanPeriod(start=start, due=today - timedelta(days=1)),
        ),
    )
    scheduler_jobs.request_overdue_reminder()
    text = raw_db.scalar(
        'SELECT text FROM library.notifications '
        "WHERE loan_id = %(id)s AND kind = 'overdue_reminder'",
        id=overdue.id,
    )
    assert text is not None
