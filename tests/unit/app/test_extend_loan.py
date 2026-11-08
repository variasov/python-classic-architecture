import logging
from datetime import date

import pytest

from library.app.commands.domain.loan import (
    LoanAlreadyReturned,
    LoanNotFound,
    LoanOverdue,
    LoanPeriod,
)
from library.app.commands.use_cases.loans.extend_loan import ExtendLoan
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date(2026, 3, 10)


def test_extend_loan_updates_due_date(
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    account,
    loan_factory,
    extend_loan_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    loan = in_memory_loans_repo.save(loan_factory())
    usecase = ExtendLoan(
        loans=in_memory_loans_repo,
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    usecase.run(account, extend_loan_params_factory(loan_id=loan.id))
    saved = in_memory_loans_repo.get_by_id(loan.id)
    assert saved.period.due == date(2026, 3, 31)
    assert len(saved.extensions) == 1
    record = caplog.records[0]
    assert record.msg == 'Продлена выдача с id=%s'
    assert record.args == (loan.id,)


def test_extend_loan_unknown_loan(
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    account,
    extend_loan_params_factory,
) -> None:
    usecase = ExtendLoan(
        loans=in_memory_loans_repo,
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    with pytest.raises(LoanNotFound):
        usecase.run(account, extend_loan_params_factory())


def test_extend_loan_overdue_loan(
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    account,
    loan_factory,
    extend_loan_params_factory,
) -> None:
    loan = in_memory_loans_repo.save(
        loan_factory(
            period=LoanPeriod(
                start=date(2026, 2, 1),
                due=date(2026, 2, 15),
            ),
        ),
    )
    usecase = ExtendLoan(
        loans=in_memory_loans_repo,
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    with pytest.raises(LoanOverdue):
        usecase.run(account, extend_loan_params_factory(loan_id=loan.id))


def test_extend_loan_returned_loan(
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    account,
    loan_factory,
    extend_loan_params_factory,
) -> None:
    loan = in_memory_loans_repo.save(loan_factory(returned_at=TODAY))
    usecase = ExtendLoan(
        loans=in_memory_loans_repo,
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    with pytest.raises(LoanAlreadyReturned):
        usecase.run(account, extend_loan_params_factory(loan_id=loan.id))


def test_extend_loan_requires_permission(
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    loan_factory,
    extend_loan_params_factory,
) -> None:
    loan = in_memory_loans_repo.save(loan_factory())
    usecase = ExtendLoan(
        loans=in_memory_loans_repo,
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            extend_loan_params_factory(loan_id=loan.id),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.LOANS_EDIT
