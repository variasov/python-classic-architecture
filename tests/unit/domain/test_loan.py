from collections.abc import Callable
from datetime import date, timedelta

import pytest
from classic.criteria import Criteria
from hypothesis import given
from hypothesis import strategies as st

from library.app.domain.loan import (
    Extension,
    ExtensionNotForward,
    Loan,
    LoanAlreadyReturned,
    LoanNotFound,
    LoanOverdue,
    LoanPeriod,
    LoanPeriodInvalid,
    LoanReturnedBeforeIssue,
    TooManyExtensions,
)

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)
NEXT_WEEK = TODAY + timedelta(days=7)


def test_valid_loan_passes_check(loan_factory: Callable[..., Loan]) -> None:
    loan_factory().check()


def test_period_due_must_be_after_start() -> None:
    with pytest.raises(LoanPeriodInvalid):
        LoanPeriod(start=TODAY, due=TODAY).check()
    with pytest.raises(LoanPeriodInvalid):
        LoanPeriod(start=TODAY, due=YESTERDAY).check()

    LoanPeriod(start=TODAY, due=TOMORROW).check()


@given(
    st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 1, 1)),
    st.integers(min_value=-400, max_value=400),
)
def test_period_check_accepts_exactly_forward_due(
    start: date,
    offset: int,
) -> None:
    due = start + timedelta(days=offset)
    period = LoanPeriod(start=start, due=due)

    if due > start:
        period.check()
    else:
        with pytest.raises(LoanPeriodInvalid):
            period.check()


def test_two_extensions_pass_check(loan_factory: Callable[..., Loan]) -> None:
    loan = loan_factory(
        extensions=[
            Extension(
                extended_at=TODAY + timedelta(days=14),
                new_due=TODAY + timedelta(days=21),
            ),
            Extension(
                extended_at=TODAY + timedelta(days=21),
                new_due=TODAY + timedelta(days=28),
            ),
        ],
    )

    loan.check()


def test_more_than_two_extensions_are_rejected(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(
        extensions=[
            Extension(extended_at=TOMORROW, new_due=NEXT_WEEK),
            Extension(
                extended_at=NEXT_WEEK,
                new_due=NEXT_WEEK + timedelta(days=7),
            ),
            Extension(
                extended_at=NEXT_WEEK + timedelta(days=7),
                new_due=NEXT_WEEK + timedelta(days=14),
            ),
        ],
    )

    with pytest.raises(TooManyExtensions):
        loan.check()


@pytest.mark.parametrize(
    'new_due',
    [TODAY + timedelta(days=Loan.TERM_DAYS), TODAY],
)
def test_extension_must_move_due_strictly_forward(
    loan_factory: Callable[..., Loan],
    new_due: date,
) -> None:
    loan = loan_factory(
        extensions=[Extension(extended_at=TOMORROW, new_due=new_due)],
    )

    with pytest.raises(ExtensionNotForward):
        loan.check()


def test_second_extension_compares_with_previous_due(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(
        period=LoanPeriod(start=TODAY, due=TOMORROW),
        extensions=[
            Extension(extended_at=TODAY, new_due=NEXT_WEEK),
            Extension(extended_at=NEXT_WEEK, new_due=NEXT_WEEK),
        ],
    )

    with pytest.raises(ExtensionNotForward):
        loan.check()


def test_returned_at_cannot_be_before_start(
    loan_factory: Callable[..., Loan],
) -> None:
    with pytest.raises(LoanReturnedBeforeIssue):
        loan_factory(returned_at=YESTERDAY).check()


@pytest.mark.parametrize('returned_at', [TODAY, TOMORROW])
def test_returned_at_not_before_start_is_allowed(
    loan_factory: Callable[..., Loan],
    returned_at: date,
) -> None:
    loan_factory(returned_at=returned_at).check()


def test_overdue_on_instance(loan_factory: Callable[..., Loan]) -> None:
    assert loan_factory(period=LoanPeriod(TODAY, YESTERDAY)).overdue(on=TODAY)
    assert not loan_factory(period=LoanPeriod(TODAY, TODAY)).overdue(on=TODAY)
    assert not loan_factory(
        period=LoanPeriod(TODAY, YESTERDAY),
        returned_at=TODAY,
    ).overdue(on=TODAY)


@given(
    st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 1, 1)),
    st.integers(min_value=-10, max_value=40),
    st.integers(min_value=0, max_value=40),
)
def test_overdue_boundary(start: date, due_offset: int, on_offset: int) -> None:
    due = start + timedelta(days=due_offset)
    on = start + timedelta(days=on_offset)
    loan = Loan(
        reader_id=1,
        copy_id=1,
        period=LoanPeriod(start=start, due=due),
    )

    if due > start:
        assert loan.overdue(on=on) is (due < on)
        assert loan.returned() is False


def test_returned_on_instance(loan_factory: Callable[..., Loan]) -> None:
    assert loan_factory(returned_at=TODAY).returned()
    assert not loan_factory().returned()


def test_due_within_on_instance(loan_factory: Callable[..., Loan]) -> None:
    loan = loan_factory(period=LoanPeriod(start=TODAY, due=NEXT_WEEK))

    assert loan.due_within(on=TODAY, days=7)
    assert loan.due_within(on=NEXT_WEEK, days=0)
    assert not loan.due_within(on=TOMORROW, days=5)
    assert not loan.due_within(on=TODAY, days=6)


@given(
    st.integers(min_value=0, max_value=30),
    st.integers(min_value=-5, max_value=35),
)
def test_due_within_boundaries(days: int, due_offset: int) -> None:
    due = TODAY + timedelta(days=due_offset)
    loan = Loan(
        reader_id=1,
        copy_id=1,
        period=LoanPeriod(start=TODAY, due=due),
    )

    assert loan.due_within(on=TODAY, days=days) is (0 <= due_offset <= days)


def test_due_within_ignores_returned_loan(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(
        period=LoanPeriod(start=TODAY, due=NEXT_WEEK),
        returned_at=TOMORROW,
    )

    assert not loan.due_within(on=TODAY, days=7)


def test_of_reader_on_instance(loan_factory: Callable[..., Loan]) -> None:
    loan = loan_factory(reader_id=5)

    assert loan.of_reader(5)
    assert not loan.of_reader(6)


def test_criteria_lazy_form(loan_factory: Callable[..., Loan]) -> None:
    loan = loan_factory(
        reader_id=5,
        period=LoanPeriod(start=TODAY, due=YESTERDAY),
    )

    assert isinstance(Loan.overdue(on=TODAY), Criteria)
    assert Loan.overdue(on=TODAY).is_satisfied_by(loan) is True
    assert Loan.returned().is_satisfied_by(loan) is False
    assert Loan.due_within(on=TODAY, days=7).is_satisfied_by(loan) is False
    assert Loan.of_reader(reader_id=5).is_satisfied_by(loan) is True


def test_criteria_combinations(loan_factory: Callable[..., Loan]) -> None:
    overdue = loan_factory(
        reader_id=5,
        period=LoanPeriod(start=TODAY, due=YESTERDAY),
    )
    active = loan_factory(
        reader_id=5,
        period=LoanPeriod(start=TODAY, due=NEXT_WEEK),
    )
    returned = loan_factory(
        reader_id=6,
        period=LoanPeriod(start=TODAY, due=YESTERDAY),
        returned_at=TODAY,
    )

    overdue_and_not_returned = Loan.overdue(on=TODAY) & ~Loan.returned()
    of_reader_and_overdue = Loan.of_reader(reader_id=5) & Loan.overdue(on=TODAY)
    due_within_or_returned = Loan.due_within(on=TODAY, days=7) | Loan.returned()
    other_readers = ~Loan.of_reader(reader_id=5)

    assert overdue_and_not_returned.is_satisfied_by(overdue) is True
    assert overdue_and_not_returned.is_satisfied_by(returned) is False
    assert of_reader_and_overdue.is_satisfied_by(overdue) is True
    assert of_reader_and_overdue.is_satisfied_by(active) is False
    assert due_within_or_returned.is_satisfied_by(active) is True
    assert due_within_or_returned.is_satisfied_by(returned) is True
    assert due_within_or_returned.is_satisfied_by(overdue) is False
    assert other_readers.is_satisfied_by(returned) is True
    assert other_readers.is_satisfied_by(active) is False


def test_loan_not_found_message_uses_id() -> None:
    assert '7' in str(LoanNotFound(id=7))


def test_extend_moves_due_and_adds_extension(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory()
    initial_due = loan.period.due

    loan.extend(on=TOMORROW, days=7)

    assert loan.period == LoanPeriod(start=TODAY, due=initial_due + timedelta(days=7))
    assert loan.extensions == [
        Extension(extended_at=TOMORROW, new_due=initial_due + timedelta(days=7)),
    ]
    loan.check()


def test_two_extensions_are_allowed(loan_factory: Callable[..., Loan]) -> None:
    loan = loan_factory()
    first_due = loan.period.due

    loan.extend(on=TOMORROW, days=7)
    loan.extend(on=first_due + timedelta(days=7), days=7)

    loan.check()
    assert len(loan.extensions) == 2
    assert loan.period.due == first_due + timedelta(days=14)


def test_third_extension_is_caught_by_check(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory()

    loan.extend(on=TOMORROW, days=7)
    loan.extend(on=TOMORROW, days=7)
    loan.extend(on=TOMORROW, days=7)

    with pytest.raises(TooManyExtensions):
        loan.check()


def test_returned_loan_cannot_be_extended(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(returned_at=TOMORROW)

    with pytest.raises(LoanAlreadyReturned):
        loan.extend(on=TOMORROW, days=7)

    assert loan.extensions == []


def test_overdue_loan_cannot_be_extended(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(period=LoanPeriod(start=TODAY, due=YESTERDAY))

    with pytest.raises(LoanOverdue):
        loan.extend(on=TODAY, days=7)

    assert loan.extensions == []
    assert loan.period.due == YESTERDAY


def test_loan_due_today_can_be_extended(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(
        period=LoanPeriod(
            start=TODAY - timedelta(days=Loan.TERM_DAYS),
            due=TODAY,
        ),
    )

    loan.extend(on=TODAY, days=7)

    loan.check()
    assert loan.period.due == TODAY + timedelta(days=7)


def test_close_sets_returned_at(loan_factory: Callable[..., Loan]) -> None:
    loan = loan_factory()

    loan.close(on=TOMORROW)

    assert loan.returned_at == TOMORROW
    assert loan.returned()
    loan.check()


def test_repeated_close_raises(loan_factory: Callable[..., Loan]) -> None:
    loan = loan_factory()
    loan.close(on=TODAY)

    with pytest.raises(LoanAlreadyReturned):
        loan.close(on=TOMORROW)

    assert loan.returned_at == TODAY


def test_close_before_issue_is_caught_by_check(
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory()

    loan.close(on=YESTERDAY)

    with pytest.raises(LoanReturnedBeforeIssue):
        loan.check()


def test_extend_and_close_errors_have_messages() -> None:
    assert '7' in str(LoanAlreadyReturned(loan_id=7))
    assert '7' in str(LoanOverdue(loan_id=7))
