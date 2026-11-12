import logging
from collections.abc import Callable
from datetime import date, timedelta

import pytest

from library.app.commands.loans.return_loan import (
    ReturnLoan,
    ReturnLoanParams,
)
from library.app.domain.copy import CopiesRepo, Copy
from library.app.domain.loan import (
    Loan,
    LoanAlreadyReturned,
    LoanNotFound,
    LoanPeriod,
    LoansRepo,
)
from library.app.domain.return_copy import ReturnCopy
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date.today()


@pytest.fixture
def loans_repo(in_memory_loans_repo: LoansRepo) -> LoansRepo:
    return in_memory_loans_repo


@pytest.fixture
def copies_repo(in_memory_copies_repo: CopiesRepo) -> CopiesRepo:
    return in_memory_copies_repo


@pytest.fixture
def return_loan(loans_repo: LoansRepo, copies_repo: CopiesRepo) -> ReturnLoan:
    return ReturnLoan(
        return_copy=ReturnCopy(loans=loans_repo, copies=copies_repo),
        logger=logging.getLogger('test'),
    )


@pytest.fixture
def loans_account() -> Account:
    return Account(login='admin', permissions=(Permissions.LOANS_EDIT,))


@pytest.fixture
def no_loans_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.BOOKS_EDIT,))


@pytest.fixture
def copy(copies_repo: CopiesRepo, copy_factory: Callable[..., Copy]) -> Copy:
    return copies_repo.save(copy_factory(is_available=False))


@pytest.fixture
def loan(
    loans_repo: LoansRepo,
    copy: Copy,
    loan_factory: Callable[..., Loan],
) -> Loan:
    assert copy.id is not None
    return loans_repo.save(
        loan_factory(
            copy_id=copy.id,
            period=LoanPeriod(
                start=TODAY - timedelta(days=7),
                due=TODAY + timedelta(days=7),
            ),
        ),
    )


def _id(loan: Loan) -> int:
    assert loan.id is not None
    return loan.id


def _copy_id(copy: Copy) -> int:
    assert copy.id is not None
    return copy.id


def test_returns_copy_for_today(
    return_loan: ReturnLoan,
    loans_account: Account,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
    loan: Loan,
    copy: Copy,
) -> None:
    return_loan.run(ReturnLoanParams(loan_id=_id(loan)), loans_account)

    loaded_loan = loans_repo.get_by_id(_id(loan))
    assert loaded_loan.returned_at == TODAY
    assert loaded_loan.returned()
    assert copies_repo.get_by_id(_copy_id(copy)).is_available is True


def test_missing_loan_raises(
    return_loan: ReturnLoan,
    loans_account: Account,
    copies_repo: CopiesRepo,
    copy: Copy,
) -> None:
    with pytest.raises(LoanNotFound):
        return_loan.run(ReturnLoanParams(loan_id=987654), loans_account)

    assert copies_repo.get_by_id(_copy_id(copy)).is_available is False


def test_requires_permission_before_storage(
    return_loan: ReturnLoan,
    no_loans_permission: Account,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
    loan: Loan,
    copy: Copy,
) -> None:
    with pytest.raises(PermissionDenied):
        return_loan.run(
            ReturnLoanParams(loan_id=_id(loan)),
            no_loans_permission,
        )

    assert loans_repo.get_by_id(_id(loan)).returned_at is None
    assert copies_repo.get_by_id(_copy_id(copy)).is_available is False


def test_repeated_return_raises(
    return_loan: ReturnLoan,
    loans_account: Account,
    loan: Loan,
) -> None:
    params = ReturnLoanParams(loan_id=_id(loan))
    return_loan.run(params, loans_account)

    with pytest.raises(LoanAlreadyReturned):
        return_loan.run(params, loans_account)
