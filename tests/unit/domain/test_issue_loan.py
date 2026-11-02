from datetime import date, timedelta

import pytest
from library.app.commands.domain.book import (
    Book,
    BooksRepo,
    CopyNotAvailable,
    ShelfLocation,
)
from library.app.commands.domain.issue_loan import (
    IssueLoan,
    LoanLimitExceeded,
    ReaderCannotBorrow,
    ReaderHasOverdueLoans,
)
from library.app.commands.domain.loan import Loan, LoanPeriod, LoansRepo
from library.app.commands.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReadersRepo,
)
from library.app.commands.domain.return_loan import ReturnLoan

TODAY = date(2026, 6, 15)


@pytest.fixture
def issue_loan(
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
    in_memory_loans_repo: LoansRepo,
) -> IssueLoan:
    return IssueLoan(
        readers=in_memory_readers_repo,
        books=in_memory_books_repo,
        loans=in_memory_loans_repo,
    )


def add_reader(
    repo: ReadersRepo,
    tier: str = 'basic',
    *,
    is_blocked: bool = False,
) -> int:
    reader = Reader(
        full_name='Иван',
        contact=Contact(email='i@e.com'),
        membership=Membership(tier=tier, valid_until=TODAY),
        is_blocked=is_blocked,
    )
    saved_id = repo.save(reader).id
    assert saved_id is not None
    return saved_id


def add_book(repo: BooksRepo, copies: int = 1) -> int:
    book = Book(isbn='9785171183660', title='T', authors=['A'], published_year=2000)
    for number in range(copies):
        book.add_copy(f'INV-{number}', ShelfLocation(hall='A', rack=1, shelf=1))
    saved_id = repo.save(book).id
    assert saved_id is not None
    return saved_id


def test_issue_takes_copy_and_creates_loan(
    issue_loan: IssueLoan,
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
    in_memory_loans_repo: LoansRepo,
) -> None:
    reader_id = add_reader(in_memory_readers_repo)
    book_id = add_book(in_memory_books_repo)
    loan = issue_loan.run(reader_id, book_id, 'INV-0', TODAY, days=14)
    assert loan.period == LoanPeriod(start=TODAY, due=TODAY + timedelta(days=14))
    assert not in_memory_books_repo.get_by_id(book_id).copies[0].is_available
    assert loan.id is not None
    assert in_memory_loans_repo.get_by_id(loan.id).reader_id == reader_id


def test_blocked_reader_cannot_borrow(
    issue_loan: IssueLoan,
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
) -> None:
    reader_id = add_reader(in_memory_readers_repo, is_blocked=True)
    book_id = add_book(in_memory_books_repo)
    with pytest.raises(ReaderCannotBorrow):
        issue_loan.run(reader_id, book_id, 'INV-0', TODAY, days=14)


def test_expired_membership_boundary(
    issue_loan: IssueLoan,
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
) -> None:
    reader_id = add_reader(in_memory_readers_repo)
    book_id = add_book(in_memory_books_repo, copies=2)
    issue_loan.run(reader_id, book_id, 'INV-0', TODAY, days=14)
    with pytest.raises(ReaderCannotBorrow):
        issue_loan.run(reader_id, book_id, 'INV-1', TODAY + timedelta(days=1), days=14)


def test_unavailable_copy(
    issue_loan: IssueLoan,
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
) -> None:
    reader_id = add_reader(in_memory_readers_repo)
    other_id = add_reader(in_memory_readers_repo)
    book_id = add_book(in_memory_books_repo)
    issue_loan.run(reader_id, book_id, 'INV-0', TODAY, days=14)
    with pytest.raises(CopyNotAvailable):
        issue_loan.run(other_id, book_id, 'INV-0', TODAY, days=14)


def test_loan_limit_by_tier(
    issue_loan: IssueLoan,
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
) -> None:
    reader_id = add_reader(in_memory_readers_repo)
    book_id = add_book(in_memory_books_repo, copies=4)
    for number in range(3):
        issue_loan.run(reader_id, book_id, f'INV-{number}', TODAY, days=14)
    with pytest.raises(LoanLimitExceeded):
        issue_loan.run(reader_id, book_id, 'INV-3', TODAY, days=14)


def test_overdue_loan_blocks_new_issue(
    issue_loan: IssueLoan,
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
    in_memory_loans_repo: LoansRepo,
) -> None:
    reader_id = add_reader(in_memory_readers_repo, tier='premium')
    book_id = add_book(in_memory_books_repo)
    in_memory_loans_repo.save(
        Loan(
            reader_id=reader_id,
            book_id=book_id,
            inventory_number='X',
            issued_at=TODAY - timedelta(days=30),
            period=LoanPeriod(
                start=TODAY - timedelta(days=30),
                due=TODAY - timedelta(days=1),
            ),
        ),
    )
    with pytest.raises(ReaderHasOverdueLoans):
        issue_loan.run(reader_id, book_id, 'INV-0', TODAY, days=14)


def test_return_loan_closes_loan_and_returns_copy(
    issue_loan: IssueLoan,
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
    in_memory_loans_repo: LoansRepo,
) -> None:
    reader_id = add_reader(in_memory_readers_repo)
    book_id = add_book(in_memory_books_repo)
    loan = issue_loan.run(reader_id, book_id, 'INV-0', TODAY, days=14)
    assert loan.id is not None
    ReturnLoan(loans=in_memory_loans_repo, books=in_memory_books_repo).run(
        loan.id,
        TODAY,
    )
    assert in_memory_loans_repo.get_by_id(loan.id).returned()
    assert in_memory_books_repo.get_by_id(book_id).copies[0].is_available
