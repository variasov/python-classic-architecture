import logging
from collections.abc import Callable
from datetime import date, timedelta

import pytest
from classic.criteria import ReturnsTrue
from classic.signals import Hub

from library.app.commands.loans.issue_loan import (
    IssueLoan,
    IssueLoanParams,
)
from library.app.commands.signals import LoanIssued
from library.app.domain.borrow_copy import (
    BorrowCopy,
    LoanLimitReached,
    ReaderCannotBorrow,
)
from library.app.domain.copy import CopiesRepo, Copy
from library.app.domain.loan import Loan, LoanPeriod, LoansRepo
from library.app.domain.reader import (
    Membership,
    Reader,
    ReadersRepo,
)
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date.today()
FUTURE = TODAY + timedelta(days=365)


@pytest.fixture
def readers_repo(in_memory_readers_repo: ReadersRepo) -> ReadersRepo:
    return in_memory_readers_repo


@pytest.fixture
def copies_repo(in_memory_copies_repo: CopiesRepo) -> CopiesRepo:
    return in_memory_copies_repo


@pytest.fixture
def loans_repo(in_memory_loans_repo: LoansRepo) -> LoansRepo:
    return in_memory_loans_repo


@pytest.fixture
def received() -> list[LoanIssued]:
    return []


@pytest.fixture
def hub(received: list[LoanIssued]) -> Hub:
    hub = Hub()
    hub.add_reaction(LoanIssued, received.append)
    return hub


@pytest.fixture
def borrow_copy(
    readers_repo: ReadersRepo,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
) -> BorrowCopy:
    return BorrowCopy(
        readers=readers_repo,
        copies=copies_repo,
        loans=loans_repo,
    )


@pytest.fixture
def issue_loan(borrow_copy: BorrowCopy, hub: Hub) -> IssueLoan:
    return IssueLoan(
        borrow_copy=borrow_copy,
        hub=hub,
        logger=logging.getLogger('test'),
    )


@pytest.fixture
def loans_account() -> Account:
    return Account(login='admin', permissions=(Permissions.LOANS_EDIT,))


@pytest.fixture
def no_loans_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.BOOKS_EDIT,))


@pytest.fixture
def issue_loan_params() -> Callable[..., IssueLoanParams]:
    def factory(**overrides: object) -> IssueLoanParams:
        fields: dict[str, object] = {'reader_id': 1, 'copy_id': 1}
        fields.update(overrides)
        return IssueLoanParams(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def reader(readers_repo: ReadersRepo, reader_factory: Callable[..., Reader]) -> Reader:
    return readers_repo.save(
        reader_factory(
            membership=Membership(tier='basic', valid_until=FUTURE),
        ),
    )


@pytest.fixture
def copy(copies_repo: CopiesRepo, copy_factory: Callable[..., Copy]) -> Copy:
    return copies_repo.save(copy_factory())


def _id(reader: Reader | Copy) -> int:
    assert reader.id is not None
    return reader.id


def test_issues_loan_for_today(
    issue_loan: IssueLoan,
    issue_loan_params: Callable[..., IssueLoanParams],
    loans_account: Account,
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
) -> None:
    created = issue_loan.run(
        issue_loan_params(reader_id=_id(reader), copy_id=_id(copy)),
        loans_account,
    )

    loan = loans_repo.get_by_id(created.id)
    assert loan.reader_id == reader.id
    assert loan.copy_id == copy.id
    assert loan.period == LoanPeriod(
        start=TODAY,
        due=TODAY + timedelta(days=Loan.TERM_DAYS),
    )
    assert copies_repo.get_by_id(_id(copy)).is_available is False


def test_emits_loan_issued(
    issue_loan: IssueLoan,
    issue_loan_params: Callable[..., IssueLoanParams],
    loans_account: Account,
    reader: Reader,
    copy: Copy,
    received: list[LoanIssued],
) -> None:
    created = issue_loan.run(
        issue_loan_params(reader_id=_id(reader), copy_id=_id(copy)),
        loans_account,
    )

    assert received == [
        LoanIssued(loan_id=created.id, reader_id=_id(reader)),
    ]


def test_requires_permission_before_storage(
    issue_loan: IssueLoan,
    issue_loan_params: Callable[..., IssueLoanParams],
    no_loans_permission: Account,
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
    received: list[LoanIssued],
) -> None:
    with pytest.raises(PermissionDenied):
        issue_loan.run(
            issue_loan_params(reader_id=_id(reader), copy_id=_id(copy)),
            no_loans_permission,
        )

    assert loans_repo.find(ReturnsTrue()) == []
    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert received == []


def test_blocked_reader_is_rejected(
    issue_loan: IssueLoan,
    issue_loan_params: Callable[..., IssueLoanParams],
    loans_account: Account,
    reader_factory: Callable[..., Reader],
    readers_repo: ReadersRepo,
    copy: Copy,
) -> None:
    blocked = readers_repo.save(
        reader_factory(
            membership=Membership(tier='basic', valid_until=FUTURE),
            is_blocked=True,
        ),
    )

    with pytest.raises(ReaderCannotBorrow):
        issue_loan.run(
            issue_loan_params(reader_id=_id(blocked), copy_id=_id(copy)),
            loans_account,
        )


def test_loan_limit_is_enforced(
    issue_loan: IssueLoan,
    issue_loan_params: Callable[..., IssueLoanParams],
    loans_account: Account,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
) -> None:
    for copy_index in range(reader.membership.loan_limit):
        loans_repo.save(
            loan_factory(
                reader_id=_id(reader),
                copy_id=100 + copy_index,
                period=LoanPeriod(
                    start=TODAY - timedelta(days=30),
                    due=TODAY + timedelta(days=7),
                ),
            ),
        )

    with pytest.raises(LoanLimitReached):
        issue_loan.run(
            issue_loan_params(reader_id=_id(reader), copy_id=_id(copy)),
            loans_account,
        )

    assert len(loans_repo.find(ReturnsTrue())) == 3
