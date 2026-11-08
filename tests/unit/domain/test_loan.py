from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from library.app.commands.domain.loan import (
    Extension,
    ExtensionDaysNotPositive,
    ExtensionNotForward,
    ExtensionsInconsistent,
    Loan,
    LoanAlreadyReturned,
    LoanOverdue,
    LoanPeriod,
    LoanPeriodInvalid,
    ReturnBeforeIssue,
    TooManyExtensions,
)

START = date(2026, 3, 10)
DUE = date(2026, 3, 24)


def test_valid_loan_period_passes_check() -> None:
    LoanPeriod(start=START, due=DUE).check()


def test_loan_period_with_equal_dates_is_invalid() -> None:
    with pytest.raises(LoanPeriodInvalid) as exc_info:
        LoanPeriod(start=START, due=START).check()
    assert exc_info.value.start == START
    assert exc_info.value.due == START


def test_loan_period_earlier_due_is_invalid() -> None:
    with pytest.raises(LoanPeriodInvalid) as exc_info:
        LoanPeriod(start=DUE, due=START).check()
    assert exc_info.value.start == DUE
    assert exc_info.value.due == START


def test_extended_period_moves_due_forward() -> None:
    period = LoanPeriod(start=START, due=DUE).extended(days=5)
    assert period.start == START
    assert period.due == date(2026, 3, 29)


def test_valid_loan_passes_check(loan_factory) -> None:
    loan_factory().check()


def test_too_many_extensions_is_invalid(loan_factory) -> None:
    loan = loan_factory(
        id=7,
        period=LoanPeriod(start=START, due=date(2026, 4, 3)),
        extensions=[
            Extension(extended_at=START, new_due=date(2026, 3, 29)),
            Extension(extended_at=START, new_due=date(2026, 4, 3)),
            Extension(extended_at=START, new_due=date(2026, 4, 8)),
        ],
    )
    with pytest.raises(TooManyExtensions) as exc_info:
        loan.check()
    assert exc_info.value.loan_id == 7


def test_extension_not_forward_is_invalid(loan_factory) -> None:
    loan = loan_factory(
        id=7,
        period=LoanPeriod(start=START, due=DUE),
        extensions=[Extension(extended_at=START, new_due=START)],
    )
    with pytest.raises(ExtensionNotForward) as exc_info:
        loan.check()
    assert exc_info.value.loan_id == 7
    assert exc_info.value.new_due == START


def test_extensions_must_match_current_period(loan_factory) -> None:
    loan = loan_factory(
        id=7,
        period=LoanPeriod(start=START, due=DUE),
        extensions=[Extension(extended_at=START, new_due=date(2026, 3, 20))],
    )
    with pytest.raises(ExtensionsInconsistent) as exc_info:
        loan.check()
    assert exc_info.value.loan_id == 7


def test_returned_before_issued_is_invalid(loan_factory) -> None:
    loan = loan_factory(id=7, returned_at=date(2026, 3, 1))
    with pytest.raises(ReturnBeforeIssue) as exc_info:
        loan.check()
    assert exc_info.value.loan_id == 7
    assert exc_info.value.issued_at == START
    assert exc_info.value.returned_at == date(2026, 3, 1)


def test_two_extensions_are_valid(loan_factory) -> None:
    loan = loan_factory(
        period=LoanPeriod(start=START, due=date(2026, 4, 7)),
        extensions=[
            Extension(extended_at=START, new_due=date(2026, 3, 31)),
            Extension(extended_at=START, new_due=date(2026, 4, 7)),
        ],
    )
    loan.check()


def test_returned_on_issued_date_is_valid(loan_factory) -> None:
    loan_factory(returned_at=START).check()


def test_extend_moves_period_and_adds_extension(loan_factory) -> None:
    loan = loan_factory()
    loan.extend(on=START, days=7)
    assert loan.period.due == date(2026, 3, 31)
    assert len(loan.extensions) == 1
    assert loan.extensions[0].new_due == date(2026, 3, 31)
    assert loan.extensions[0].extended_at == START


@given(st.integers(min_value=1, max_value=60))
def test_extend_any_positive_number_of_days(days: int) -> None:
    loan = Loan(
        reader_id=1,
        book_id=1,
        inventory_number='INV-1',
        issued_at=START,
        period=LoanPeriod(start=START, due=DUE),
    )
    loan.extend(on=START, days=days)
    assert (loan.period.due - DUE).days == days


@pytest.mark.parametrize('days', [0, -1, -100])
def test_extend_by_non_positive_days_raises(days: int, loan_factory) -> None:
    with pytest.raises(ExtensionDaysNotPositive) as exc_info:
        loan_factory().extend(on=START, days=days)
    assert str(exc_info.value) == 'Срок продления должен быть положительным'


def test_extend_returned_loan_raises(loan_factory) -> None:
    loan = loan_factory(id=7, returned_at=START)
    with pytest.raises(LoanAlreadyReturned) as exc_info:
        loan.extend(on=START, days=5)
    assert exc_info.value.loan_id == 7


def test_extend_overdue_loan_raises(loan_factory) -> None:
    loan = loan_factory(id=7)
    with pytest.raises(LoanOverdue) as exc_info:
        loan.extend(on=date(2026, 3, 25), days=5)
    assert exc_info.value.loan_id == 7


def test_extend_loan_twice_reaches_max(loan_factory) -> None:
    loan = loan_factory(id=7)
    loan.extend(on=START, days=1)
    loan.extend(on=START, days=1)
    with pytest.raises(TooManyExtensions) as exc_info:
        loan.extend(on=START, days=1)
    assert exc_info.value.loan_id == 7


def test_close_sets_returned_at(loan_factory) -> None:
    loan = loan_factory()
    loan.close(on=date(2026, 3, 15))
    assert loan.returned_at == date(2026, 3, 15)


def test_close_returned_loan_raises(loan_factory) -> None:
    loan = loan_factory(id=7)
    loan.close(on=START)
    with pytest.raises(LoanAlreadyReturned) as exc_info:
        loan.close(on=START)
    assert exc_info.value.loan_id == 7


def test_overdue_in_both_forms(loan_factory) -> None:
    loan = loan_factory()
    assert loan.overdue(on=date(2026, 3, 25))
    assert not loan.overdue(on=DUE)
    assert Loan.overdue(on=date(2026, 3, 25)).is_satisfied_by(loan)


def test_returned_loan_is_not_overdue(loan_factory) -> None:
    loan = loan_factory(returned_at=date(2026, 3, 11))
    assert not loan.overdue(on=date(2026, 3, 25))
    assert not Loan.overdue(on=date(2026, 3, 25)).is_satisfied_by(loan)


def test_returned_in_both_forms(loan_factory) -> None:
    loan = loan_factory(returned_at=date(2026, 3, 11))
    assert loan.returned()
    assert Loan.returned().is_satisfied_by(loan)
    assert not loan_factory().returned()


def test_due_within_boundaries(loan_factory) -> None:
    loan = loan_factory()
    assert loan.due_within(on=START, days=14)
    assert loan.due_within(on=DUE, days=0)
    assert not loan.due_within(on=date(2026, 3, 9), days=14)
    assert not loan.due_within(on=START, days=13)
    assert Loan.due_within(on=START, days=14).is_satisfied_by(loan)


def test_due_within_is_false_for_returned_loan(loan_factory) -> None:
    loan = loan_factory(returned_at=START)
    assert not loan.due_within(on=START, days=14)


def test_belongs_to_reader_in_both_forms(loan_factory) -> None:
    loan = loan_factory(reader_id=7)
    assert loan.belongs_to_reader(reader_id=7)
    assert not loan.belongs_to_reader(reader_id=8)
    assert Loan.belongs_to_reader(reader_id=7).is_satisfied_by(loan)


def test_loan_criteria_combinations(loan_factory) -> None:
    loan = loan_factory()
    combined = (
        Loan.overdue(on=date(2026, 3, 25))
        & Loan.belongs_to_reader(reader_id=1)
    )
    assert combined.is_satisfied_by(loan)
    either = (
        Loan.overdue(on=date(2026, 3, 25)) | Loan.returned()
    )
    assert either.is_satisfied_by(loan)
    assert (
        Loan.belongs_to_reader(reader_id=1) & ~Loan.returned()
    ).is_satisfied_by(loan)


def test_loan_period_is_frozen() -> None:
    period = LoanPeriod(start=START, due=DUE)
    with pytest.raises(AttributeError):
        period.due = START  # type: ignore[misc]


def test_extension_is_frozen() -> None:
    extension = Extension(extended_at=START, new_due=DUE)
    with pytest.raises(AttributeError):
        extension.new_due = START  # type: ignore[misc]


def test_loan_defaults_id_is_none(loan_factory) -> None:
    assert loan_factory().id is None


def test_loan_type_is_loan(loan_factory) -> None:
    assert isinstance(loan_factory(), Loan)
