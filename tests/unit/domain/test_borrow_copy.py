from collections.abc import Callable
from datetime import date, timedelta

import pytest
from classic.criteria import ReturnsTrue

from library.app.domain.borrow_copy import (
    BorrowCopy,
    LoanLimitReached,
    ReaderCannotBorrow,
    ReaderHasOverdueLoans,
)
from library.app.domain.copy import CopiesRepo, Copy, CopyNotAvailable
from library.app.domain.loan import (
    Loan,
    LoanPeriod,
    LoansRepo,
)
from library.app.domain.reader import (
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


def test_issues_copy(
    borrow_copy: BorrowCopy,
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
    copies_repo: CopiesRepo,
) -> None:
    loan = borrow_copy.run(
        reader_id=_id(reader),
        copy_id=_id(copy),
        on=TODAY,
    )

    assert loan.id is not None
    assert loan.reader_id == reader.id
    assert loan.copy_id == copy.id
    assert loan.period == LoanPeriod(
        start=TODAY,
        due=TODAY + timedelta(days=Loan.TERM_DAYS),
    )
    assert loan.returned_at is None
    assert loan.extensions == []
    assert loans_repo.get_by_id(loan.id) == loan
    assert copies_repo.get_by_id(_id(copy)).is_available is False


def test_inactive_membership_is_rejected(
    borrow_copy: BorrowCopy,
    reader_factory: Callable[..., Reader],
    readers_repo: ReadersRepo,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
) -> None:
    reader = readers_repo.save(
        reader_factory(
            membership=Membership(tier='basic', valid_until=YESTERDAY),
        ),
    )

    with pytest.raises(ReaderCannotBorrow):
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert loans_repo.find(ReturnsTrue()) == []


def test_blocked_reader_is_rejected(
    borrow_copy: BorrowCopy,
    reader_factory: Callable[..., Reader],
    readers_repo: ReadersRepo,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
) -> None:
    reader = readers_repo.save(reader_factory(is_blocked=True))

    with pytest.raises(ReaderCannotBorrow):
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert loans_repo.find(ReturnsTrue()) == []


def test_loan_limit_is_reached(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
) -> None:
    for copy_index in range(reader.membership.loan_limit):
        loans_repo.save(
            _active_loan(
                loan_factory,
                reader_id=_id(reader),
                copy_id=100 + copy_index,
            ),
        )

    with pytest.raises(LoanLimitReached) as error:
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert error.value.limit == 3
    assert copies_repo.get_by_id(_id(copy)).is_available is True
    assert len(loans_repo.find(ReturnsTrue())) == 3


def test_returned_loans_do_not_count_towards_limit(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    loans_repo: LoansRepo,
) -> None:
    for copy_index in range(reader.membership.loan_limit):
        loans_repo.save(
            _active_loan(
                loan_factory,
                reader_id=_id(reader),
                copy_id=100 + copy_index,
                due=TOMORROW,
                returned_at=TODAY,
            ),
        )

    loan = borrow_copy.run(
        reader_id=_id(reader),
        copy_id=_id(copy),
        on=TODAY,
    )

    assert loan.id is not None


def test_overdue_loans_are_rejected(
    borrow_copy: BorrowCopy,
    loan_factory: Callable[..., Loan],
    reader: Reader,
    copy: Copy,
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
) -> None:
    loans_repo.save(
        _active_loan(
            loan_factory,
            reader_id=_id(reader),
            copy_id=100,
            due=YESTERDAY,
        ),
    )

    with pytest.raises(ReaderHasOverdueLoans):
        borrow_copy.run(reader_id=_id(reader), copy_id=_id(copy), on=TODAY)

    assert copies_repo.get_by_id(_id(copy)).is_available is True


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
        ),
    )

    loan = borrow_copy.run(
        reader_id=_id(reader),
        copy_id=_id(copy),
        on=TODAY,
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
        ),
    )

    issued = borrow_copy.run(
        reader_id=_id(reader),
        copy_id=_id(copy),
        on=TODAY,
    )

    assert issued.id is not None


def test_unavailable_copy_is_rejected(
    borrow_copy: BorrowCopy,
    reader: Reader,
    copy_factory: Callable[..., Copy],
    copies_repo: CopiesRepo,
    loans_repo: LoansRepo,
) -> None:
    unavailable = copies_repo.save(copy_factory(is_available=False))

    with pytest.raises(CopyNotAvailable):
        borrow_copy.run(
            reader_id=_id(reader),
            copy_id=_id(unavailable),
            on=TODAY,
        )

    assert loans_repo.find(ReturnsTrue()) == []
