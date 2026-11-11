from collections.abc import Callable
from datetime import date, timedelta

import pytest
from classic.criteria import ReturnsTrue
from classic.signals import Hub

from library.app.commands.domain.borrow_copy import (
    BorrowCopy,
    LoanLimitReached,
    ReaderCannotBorrow,
    ReaderHasOverdueLoans,
)
from library.app.commands.domain.copy import Copy, CopyNotAvailable, CopiesRepo
from library.app.commands.domain.events import LoanIssued
from library.app.commands.domain.loan import (
    Loan,
    LoanPeriod,
    LoansRepo,
)
from library.app.commands.domain.reader import (
    Membership,
    Reader,
    ReadersRepo,
)

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)


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
    hub: Hub,
) -> BorrowCopy:
    return BorrowCopy(
        readers=readers_repo,
        copies=copies_repo,
        loans=loans_repo,
        hub=hub,
    )


@pytest.fixture
def reader(readers_repo: ReadersRepo, reader_factory: Callable[..., Reader]) -> Reader:
    return readers_repo.save(reader_factory())


@pytest.fixture
def copy(copies_repo: CopiesRepo, copy_factory: Callable[..., Copy]) -> Copy:
    return copies_repo.save(copy_factory())


def _id(reader: Reader | Copy | Loan) -> int:
    assert reader.id is not None
    return reader.id


def _active_loan(
    loan_factory: Callable[..., Loan],
    reader_id: int,
    copy_id: int,
    due: date = TODAY,
    returned_at: date | None = None,
) -> Loan:
    return loan_factory(
        reader_id=reader_id,
        copy_id=copy_id,
        period=LoanPeriod(
            start=TODAY - timedelta(days=30),
            due=due,
        ),
        returned_at=returned_at,
    )


def test_issues_copy_and_emits_event(
    borrow_copy: BorrowCopy,
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
    received: list[LoanIssued],
) -> None:
    loan = borrow_copy.run(
        reader_id=_id(reader), copy_id=_id(copy), on=TODAY
    )

    assert loan.id is not None
    assert loan.reader_id == reader.id
    assert loan.copy_id == copy.id
    assert loan.period == LoanPeriod(
        start=TODAY, due=TODAY + timedelta(days=Loan.TERM_DAYS)
    )
    assert loan.returned_at is None
    assert loan.extensions == []
    assert loans_repo.get_by_id(loan.id) == loan
    assert copies_repo.get_by_id(_id(copy)).is_available is False
    assert received == [
        LoanIssued(loan_id=loan.id, reader_id=_id(reader))
    ]


def test_inactive_membership_is_rejected(
    borrow_copy: BorrowCopy,
    reader_factory: Callable[..., Reader],
    readers_repo: ReadersRepo,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
    received: list[LoanIssued],
) -> None:
    reader = readers_repo.save(
        reader_factory(
            membership=Membership(tier='basic', valid_until=YESTERDAY)
        )
    )

    with pytest.raises(ReaderCannotBorrow):
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert loans_repo.find(ReturnsTrue()) == []
    assert received == []


def test_blocked_reader_is_rejected(
    borrow_copy: BorrowCopy,
    reader_factory: Callable[..., Reader],
    readers_repo: ReadersRepo,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
    received: list[LoanIssued],
) -> None:
    reader = readers_repo.save(reader_factory(is_blocked=True))

    with pytest.raises(ReaderCannotBorrow):
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert loans_repo.find(ReturnsTrue()) == []
    assert received == []


def test_loan_limit_is_reached(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
    received: list[LoanIssued],
) -> None:
    for copy_index in range(reader.membership.loan_limit):
        loans_repo.save(
            _active_loan(
                loan_factory, reader_id=_id(reader), copy_id=100 + copy_index
            )
        )

    with pytest.raises(LoanLimitReached) as error:
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert error.value.limit == 3
    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert len(loans_repo.find(ReturnsTrue())) == 3
    assert received == []


def test_returned_loans_do_not_count_towards_limit(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
    received: list[LoanIssued],
) -> None:
    for copy_index in range(reader.membership.loan_limit):
        loans_repo.save(
            _active_loan(
                loan_factory,
                reader_id=_id(reader),
                copy_id=100 + copy_index,
                due=TOMORROW,
                returned_at=TODAY,
            )
        )

    loan = borrow_copy.run(
        reader_id=_id(reader), copy_id=_id(copy), on=TODAY
    )

    assert loan.id is not None
    assert received == [
        LoanIssued(loan_id=loan.id, reader_id=_id(reader))
    ]


def test_overdue_loans_are_rejected(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
    received: list[LoanIssued],
) -> None:
    loans_repo.save(
        _active_loan(
            loan_factory,
            reader_id=_id(reader),
            copy_id=100,
            due=YESTERDAY,
        )
    )

    with pytest.raises(ReaderHasOverdueLoans):
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert received == []


def test_returned_overdue_loan_does_not_block(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
) -> None:
    loans_repo.save(
        _active_loan(
            loan_factory,
            reader_id=_id(reader),
            copy_id=100,
            due=YESTERDAY,
            returned_at=TODAY,
        )
    )

    loan = borrow_copy.run(
        reader_id=_id(reader), copy_id=_id(copy), on=TODAY
    )

    assert loan.id is not None


def test_loan_due_today_is_not_overdue(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
) -> None:
    loans_repo.save(
        _active_loan(
            loan_factory,
            reader_id=_id(reader),
            copy_id=100,
            due=TODAY,
        )
    )

    issued = borrow_copy.run(
        reader_id=_id(reader), copy_id=_id(copy), on=TODAY
    )

    assert issued.id is not None


def test_unavailable_copy_is_rejected(
    borrow_copy: BorrowCopy,
    reader: Reader,
    copy_factory: Callable[..., Copy],
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
    received: list[LoanIssued],
) -> None:
    unavailable = copies_repo.save(copy_factory(is_available=False))

    with pytest.raises(CopyNotAvailable):
        borrow_copy.run(
            reader_id=_id(reader), copy_id=_id(unavailable), on=TODAY
        )

    assert loans_repo.find(ReturnsTrue()) == []
    assert received == []
