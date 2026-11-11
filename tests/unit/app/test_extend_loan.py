import logging
from collections.abc import Callable
from datetime import date, timedelta

import pytest

from library.app.commands.domain.loan import (
    Extension,
    Loan,
    LoanAlreadyReturned,
    LoanNotFound,
    LoanOverdue,
    LoanPeriod,
    LoansRepo,
    TooManyExtensions,
)
from library.app.commands.use_cases.loans.extend_loan import (
    ExtendLoan,
    ExtendLoanParams,
)
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date.today()


@pytest.fixture
def loans_repo(in_memory_loans_repo: LoansRepo) -> LoansRepo:
    return in_memory_loans_repo


@pytest.fixture
def extend_loan(loans_repo: LoansRepo) -> ExtendLoan:
    return ExtendLoan(loans=loans_repo, logger=logging.getLogger('test'))


@pytest.fixture
def loans_account() -> Account:
    return Account(login='admin', permissions=(Permissions.LOANS_EDIT,))


@pytest.fixture
def no_loans_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.BOOKS_EDIT,))


@pytest.fixture
def loan(
    loans_repo: LoansRepo, loan_factory: Callable[..., Loan]
) -> Loan:
    return loans_repo.save(
        loan_factory(
            period=LoanPeriod(
                start=TODAY, due=TODAY + timedelta(days=Loan.TERM_DAYS)
            )
        )
    )


def _id(loan: Loan) -> int:
    assert loan.id is not None
    return loan.id


def test_extends_loan_for_today(
    extend_loan: ExtendLoan,
    loans_account: Account,
    loans_repo: LoansRepo,
    loan: Loan,
) -> None:
    extend_loan.run(
        ExtendLoanParams(loan_id=_id(loan), days=7), loans_account
    )

    loaded = loans_repo.get_by_id(_id(loan))
    assert loaded.period == LoanPeriod(
        start=TODAY,
        due=TODAY + timedelta(days=Loan.TERM_DAYS + 7),
    )
    assert loaded.extensions == [
        Extension(
            extended_at=TODAY,
            new_due=TODAY + timedelta(days=Loan.TERM_DAYS + 7),
        )
    ]


def test_two_extensions_keep_loan_valid(
    extend_loan: ExtendLoan,
    loans_account: Account,
    loans_repo: LoansRepo,
    loan: Loan,
) -> None:
    params = ExtendLoanParams(loan_id=_id(loan), days=7)

    extend_loan.run(params, loans_account)
    extend_loan.run(params, loans_account)

    loaded = loans_repo.get_by_id(_id(loan))
    assert len(loaded.extensions) == 2
    assert loaded.period.due == TODAY + timedelta(
        days=Loan.TERM_DAYS + 14
    )


def test_third_extension_is_rejected_and_not_saved(
    extend_loan: ExtendLoan,
    loans_account: Account,
    loans_repo: LoansRepo,
    loan: Loan,
) -> None:
    params = ExtendLoanParams(loan_id=_id(loan), days=7)
    extend_loan.run(params, loans_account)
    extend_loan.run(params, loans_account)

    with pytest.raises(TooManyExtensions):
        extend_loan.run(params, loans_account)

    loaded = loans_repo.get_by_id(_id(loan))
    assert len(loaded.extensions) == 2


def test_missing_loan_raises(
    extend_loan: ExtendLoan,
    loans_account: Account,
) -> None:
    with pytest.raises(LoanNotFound):
        extend_loan.run(ExtendLoanParams(loan_id=987654, days=7), loans_account)


def test_returned_loan_cannot_be_extended(
    extend_loan: ExtendLoan,
    loans_account: Account,
    loans_repo: LoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loans_repo.save(loan_factory(returned_at=TODAY))

    with pytest.raises(LoanAlreadyReturned):
        extend_loan.run(ExtendLoanParams(loan_id=_id(loan), days=7), loans_account)


def test_overdue_loan_cannot_be_extended(
    extend_loan: ExtendLoan,
    loans_account: Account,
    loans_repo: LoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loans_repo.save(
        loan_factory(
            period=LoanPeriod(
                start=TODAY - timedelta(days=30),
                due=TODAY - timedelta(days=1),
            )
        )
    )

    with pytest.raises(LoanOverdue):
        extend_loan.run(ExtendLoanParams(loan_id=_id(loan), days=7), loans_account)


def test_requires_permission_before_storage(
    extend_loan: ExtendLoan,
    no_loans_permission: Account,
    loans_repo: LoansRepo,
    loan: Loan,
) -> None:
    with pytest.raises(PermissionDenied):
        extend_loan.run(
            ExtendLoanParams(loan_id=_id(loan), days=7),
            no_loans_permission,
        )

    loaded = loans_repo.get_by_id(_id(loan))
    assert loaded.extensions == []
    assert loaded.period.due == TODAY + timedelta(days=Loan.TERM_DAYS)


@pytest.mark.parametrize('days', [1, 30])
def test_days_boundaries_are_accepted(days: int) -> None:
    params = ExtendLoanParams(loan_id=1, days=days)

    assert params.days == days


@pytest.mark.parametrize('days', [0, -1, 31])
def test_days_out_of_range_raise(days: int) -> None:
    with pytest.raises(ValueError):
        ExtendLoanParams(loan_id=1, days=days)
