import logging
from datetime import date

from library.app.commands.domain.loan import LoanPeriod
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    RemindOverdueLoans,
)


def test_remind_overdue_loans_creates_notifications(
    in_memory_loans_repo,
    notifications_gateway,
    test_logger,
    loan_factory,
    remind_overdue_loans_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    in_memory_loans_repo.save(
        loan_factory(
            reader_id=1,
            period=LoanPeriod(
                start=date(2026, 2, 1),
                due=date(2026, 2, 15),
            ),
        ),
    )
    in_memory_loans_repo.save(
        loan_factory(
            reader_id=2,
            issued_at=date(2026, 2, 1),
            period=LoanPeriod(
                start=date(2026, 2, 1),
                due=date(2026, 2, 20),
            ),
        ),
    )
    in_memory_loans_repo.save(loan_factory(reader_id=3))
    usecase = RemindOverdueLoans(
        loans=in_memory_loans_repo,
        notifications=notifications_gateway,
        logger=test_logger,
    )
    count = usecase.run(
        remind_overdue_loans_params_factory(on=date(2026, 3, 10)),
    )
    assert count == 2
    assert len(notifications_gateway.messages) == 2
    assert 'id=1' in notifications_gateway.messages[0]
    assert 'читатель 1' in notifications_gateway.messages[0]
    record = caplog.records[0]
    assert record.msg == 'Создано напоминаний о просроченных выдачах: %s'
    assert record.args == (2,)


def test_remind_overdue_loans_without_overdue(
    in_memory_loans_repo,
    notifications_gateway,
    test_logger,
    loan_factory,
    remind_overdue_loans_params_factory,
) -> None:
    in_memory_loans_repo.save(loan_factory())
    usecase = RemindOverdueLoans(
        loans=in_memory_loans_repo,
        notifications=notifications_gateway,
        logger=test_logger,
    )
    count = usecase.run(
        remind_overdue_loans_params_factory(on=date(2026, 3, 10)),
    )
    assert count == 0
    assert notifications_gateway.messages == []


def test_remind_overdue_loans_ignores_returned(
    in_memory_loans_repo,
    notifications_gateway,
    test_logger,
    loan_factory,
    remind_overdue_loans_params_factory,
) -> None:
    in_memory_loans_repo.save(
        loan_factory(
            issued_at=date(2026, 2, 1),
            period=LoanPeriod(
                start=date(2026, 2, 1),
                due=date(2026, 2, 15),
            ),
            returned_at=date(2026, 2, 10),
        ),
    )
    usecase = RemindOverdueLoans(
        loans=in_memory_loans_repo,
        notifications=notifications_gateway,
        logger=test_logger,
    )
    count = usecase.run(
        remind_overdue_loans_params_factory(on=date(2026, 3, 10)),
    )
    assert count == 0
