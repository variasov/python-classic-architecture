from datetime import date, timedelta
from typing import Any

import pytest
from library.app.commands.domain.loan import (
    Extension,
    ExtensionDaysNotPositive,
    ExtensionNotForward,
    Loan,
    LoanAlreadyReturned,
    LoanOverdue,
    LoanPeriod,
    LoanPeriodInvalid,
    ReturnedBeforeIssued,
    TooManyExtensions,
)

START = date(2026, 6, 1)
DUE = date(2026, 6, 15)


def make_loan(**overrides: Any) -> Loan:
    fields: dict[str, Any] = {
        'reader_id': 1,
        'book_id': 1,
        'inventory_number': 'INV-1',
        'issued_at': START,
        'period': LoanPeriod(start=START, due=DUE),
    }
    return Loan(**{**fields, **overrides})


def test_valid_loan() -> None:
    make_loan().check()


def test_period_boundary() -> None:
    with pytest.raises(LoanPeriodInvalid):
        LoanPeriod(start=START, due=START).check()
    LoanPeriod(start=START, due=START + timedelta(days=1)).check()


def test_extension_not_forward() -> None:
    with pytest.raises(ExtensionNotForward):
        Extension(extended_at=START, new_due=START).check()
    loan = make_loan(
        extensions=[
            Extension(extended_at=START, new_due=date(2026, 6, 20)),
            Extension(extended_at=START, new_due=date(2026, 6, 20)),
        ],
    )
    with pytest.raises(ExtensionNotForward):
        loan.check()


def test_returned_before_issued() -> None:
    with pytest.raises(ReturnedBeforeIssued):
        make_loan(returned_at=date(2026, 5, 31)).check()
    make_loan(returned_at=START).check()


def test_extend_moves_due() -> None:
    loan = make_loan()
    loan.extend(on=DUE, days=7)
    assert loan.period.due == date(2026, 6, 22)
    assert loan.extensions == [Extension(extended_at=DUE, new_due=date(2026, 6, 22))]
    loan.check()


def test_extend_limit() -> None:
    loan = make_loan()
    loan.extend(on=START, days=1)
    loan.extend(on=START, days=1)
    with pytest.raises(TooManyExtensions):
        loan.extend(on=START, days=1)


def test_extend_overdue_boundary() -> None:
    make_loan().extend(on=DUE, days=1)
    with pytest.raises(LoanOverdue):
        make_loan().extend(on=DUE + timedelta(days=1), days=1)


def test_extend_returned() -> None:
    loan = make_loan()
    loan.close(START)
    with pytest.raises(LoanAlreadyReturned):
        loan.extend(on=START, days=1)


def test_extend_non_positive_days() -> None:
    with pytest.raises(ExtensionDaysNotPositive):
        make_loan().extend(on=START, days=0)


def test_close() -> None:
    loan = make_loan()
    loan.close(DUE)
    assert loan.returned_at == DUE
    with pytest.raises(LoanAlreadyReturned):
        loan.close(DUE)
    with pytest.raises(ReturnedBeforeIssued):
        make_loan().close(date(2026, 5, 1))


def test_criteria() -> None:
    loan = make_loan()
    assert not loan.overdue(on=DUE)
    assert loan.overdue(on=DUE + timedelta(days=1))
    assert Loan.overdue(on=DUE + timedelta(days=1)).is_satisfied_by(loan)
    assert not loan.returned()
    assert loan.due_within(on=START, days=14)
    assert not loan.due_within(on=START, days=13)
    assert Loan.of_reader(reader_id=1).is_satisfied_by(loan)
    loan.close(DUE)
    assert loan.returned()
    assert not loan.overdue(on=DUE + timedelta(days=5))
    active_overdue = ~Loan.returned() & Loan.overdue(on=DUE)
    assert not active_overdue.is_satisfied_by(loan)
    assert (Loan.returned() | Loan.overdue(on=DUE)).is_satisfied_by(loan)
