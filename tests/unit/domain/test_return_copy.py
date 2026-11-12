from collections.abc import Callable
from datetime import date

import pytest
from classic.criteria import ReturnsTrue

from library.app.domain.copy import CopiesRepo, Copy, CopyNotTaken
from library.app.domain.loan import (
    Loan,
    LoanAlreadyReturned,
    LoanNotFound,
    LoanPeriod,
    LoansRepo,
)
from library.app.domain.return_copy import ReturnCopy

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)


@pytest.fixture
def loans_repo(in_memory_loans_repo: LoansRepo) -> LoansRepo:
    return in_memory_loans_repo


@pytest.fixture
def copies_repo(in_memory_copies_repo: CopiesRepo) -> CopiesRepo:
    return in_memory_copies_repo


@pytest.fixture
def return_copy(loans_repo: LoansRepo, copies_repo: CopiesRepo) -> ReturnCopy:
    return ReturnCopy(loans=loans_repo, copies=copies_repo)


@pytest.fixture
def taken_copy(copies_repo: CopiesRepo, copy_factory: Callable[..., Copy]) -> Copy:
    return copies_repo.save(copy_factory(is_available=False))


@pytest.fixture
def loan(
    loans_repo: LoansRepo,
    taken_copy: Copy,
    loan_factory: Callable[..., Loan],
) -> Loan:
    assert taken_copy.id is not None
    return loans_repo.save(
        loan_factory(
            copy_id=taken_copy.id,
            period=LoanPeriod(start=TODAY, due=TOMORROW),
        ),
    )


def _loan_id(loan: Loan) -> int:
    assert loan.id is not None
    return loan.id


def _copy_id(copy: Copy) -> int:
    assert copy.id is not None
    return copy.id


def test_return_copy_closes_loan_and_frees_copy(
    return_copy: ReturnCopy,
    loan: Loan,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
    taken_copy: Copy,
) -> None:
    return_copy.run(_loan_id(loan), on=TOMORROW)

    loaded_loan = loans_repo.get_by_id(_loan_id(loan))
    loaded_copy = copies_repo.get_by_id(_copy_id(taken_copy))
    assert loaded_loan.returned_at == TOMORROW
    assert loaded_loan.returned()
    assert loaded_copy.is_available is True
    assert loaded_copy.available()


def test_return_copy_of_returned_loan_keeps_copy_taken(
    return_copy: ReturnCopy,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
    taken_copy: Copy,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loans_repo.save(
        loan_factory(
            copy_id=_copy_id(taken_copy),
            period=LoanPeriod(start=TODAY, due=TOMORROW),
            returned_at=TODAY,
        ),
    )

    with pytest.raises(LoanAlreadyReturned):
        return_copy.run(_loan_id(loan), on=TOMORROW)

    assert copies_repo.get_by_id(_copy_id(taken_copy)).is_available is False


def test_return_copy_of_missing_loan_raises(
    return_copy: ReturnCopy,
    copies_repo: CopiesRepo,
) -> None:
    with pytest.raises(LoanNotFound):
        return_copy.run(987654, on=TODAY)

    assert copies_repo.find(ReturnsTrue()) == []


def test_return_copy_of_available_copy_raises(
    return_copy: ReturnCopy,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
    copy_factory: Callable[..., Copy],
    loan_factory: Callable[..., Loan],
) -> None:
    copy = copies_repo.save(copy_factory(is_available=True))
    loan = loans_repo.save(
        loan_factory(
            copy_id=_copy_id(copy),
            period=LoanPeriod(start=TODAY, due=TOMORROW),
        ),
    )

    with pytest.raises(CopyNotTaken):
        return_copy.run(_loan_id(loan), on=TOMORROW)

    loaded_loan = loans_repo.get_by_id(_loan_id(loan))
    assert loaded_loan.returned_at is None
