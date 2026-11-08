from datetime import date

import pytest

from library.app.commands.domain.book import (
    BookNotFound,
    CopyNotFound,
    NoAvailableCopies,
)
from library.app.commands.domain.issue_loan import IssueLoan
from library.app.commands.domain.loan import Loan, LoanPeriod
from library.app.commands.domain.reader import (
    LoanLimitExceeded,
    Membership,
    ReaderCannotBorrow,
    ReaderHasOverdueLoans,
    ReaderNotFound,
)


def _issue_loan(
    books_repo,
    readers_repo,
    loans_repo,
) -> IssueLoan:
    return IssueLoan(
        readers=readers_repo,
        books=books_repo,
        loans=loans_repo,
    )


def test_issue_loan_success(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    loan = usecase.run(
        reader_id=reader.id,
        book_id=book.id,
        inventory_number='INV-1',
        on=date(2026, 3, 10),
    )
    assert loan.id == 1
    assert loan.reader_id == reader.id
    assert loan.book_id == book.id
    assert loan.inventory_number == 'INV-1'
    assert loan.issued_at == date(2026, 3, 10)
    assert loan.period.start == date(2026, 3, 10)
    assert loan.period.due == date(2026, 3, 24)
    saved = in_memory_loans_repo.get_by_id(loan.id)
    assert saved == loan
    assert in_memory_books_repo.get_by_id(book.id).copies[0].is_available is False


def test_issue_loan_requires_active_membership(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(
        reader_factory(
            membership=Membership(
                tier='basic',
                valid_until=date(2026, 3, 9),
            ),
        ),
    )
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(ReaderCannotBorrow) as exc_info:
        usecase.run(
            reader_id=reader.id,
            book_id=book.id,
            inventory_number='INV-1',
            on=date(2026, 3, 10),
        )
    assert exc_info.value.reader_id == reader.id


def test_issue_loan_rejects_blocked_reader(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory(is_blocked=True))
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(ReaderCannotBorrow) as exc_info:
        usecase.run(
            reader_id=reader.id,
            book_id=book.id,
            inventory_number='INV-1',
            on=date(2026, 3, 10),
        )
    assert exc_info.value.reader_id == reader.id


def test_issue_loan_respects_limit(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    for _ in range(3):
        in_memory_loans_repo.save(loan_factory(reader_id=reader.id))
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(LoanLimitExceeded) as exc_info:
        usecase.run(
            reader_id=reader.id,
            book_id=book.id,
            inventory_number='INV-1',
            on=date(2026, 3, 10),
        )
    assert exc_info.value.reader_id == reader.id
    assert exc_info.value.limit == 3


def test_issue_loan_does_not_count_returned_loans(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    for _ in range(3):
        in_memory_loans_repo.save(
            loan_factory(
                reader_id=reader.id,
                returned_at=date(2026, 3, 10),
            ),
        )
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    loan = usecase.run(
        reader_id=reader.id,
        book_id=book.id,
        inventory_number='INV-1',
        on=date(2026, 3, 10),
    )
    assert loan.reader_id == reader.id


def test_issue_loan_ignores_other_readers_active_loans(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    other = in_memory_readers_repo.save(reader_factory(full_name='Other'))
    for _ in range(3):
        in_memory_loans_repo.save(loan_factory(reader_id=other.id))
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    loan = usecase.run(
        reader_id=reader.id,
        book_id=book.id,
        inventory_number='INV-1',
        on=date(2026, 3, 10),
    )
    assert loan.reader_id == reader.id


def test_issue_loan_rejects_reader_with_overdue_loans(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    in_memory_loans_repo.save(
        loan_factory(
            reader_id=reader.id,
            issued_at=date(2026, 2, 1),
            period=LoanPeriod(
                start=date(2026, 2, 1),
                due=date(2026, 2, 15),
            ),
        ),
    )
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(ReaderHasOverdueLoans) as exc_info:
        usecase.run(
            reader_id=reader.id,
            book_id=book.id,
            inventory_number='INV-1',
            on=date(2026, 3, 10),
        )
    assert exc_info.value.reader_id == reader.id


def test_issue_loan_ignores_other_readers_overdue_loans(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    other = in_memory_readers_repo.save(reader_factory(full_name='Other'))
    in_memory_loans_repo.save(
        loan_factory(
            reader_id=other.id,
            issued_at=date(2026, 2, 1),
            period=LoanPeriod(
                start=date(2026, 2, 1),
                due=date(2026, 2, 15),
            ),
        ),
    )
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    loan = usecase.run(
        reader_id=reader.id,
        book_id=book.id,
        inventory_number='INV-1',
        on=date(2026, 3, 10),
    )
    assert loan.reader_id == reader.id


def test_issue_loan_rejects_book_without_available_copies(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    copy_factory,
    reader_factory,
) -> None:
    book = in_memory_books_repo.save(
        book_factory(copies=[copy_factory(is_available=False)]),
    )
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(NoAvailableCopies) as exc_info:
        usecase.run(
            reader_id=reader.id,
            book_id=book.id,
            inventory_number='INV-1',
            on=date(2026, 3, 10),
        )
    assert exc_info.value.book_id == book.id


def test_issue_loan_missing_copy(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(CopyNotFound):
        usecase.run(
            reader_id=reader.id,
            book_id=book.id,
            inventory_number='MISSING',
            on=date(2026, 3, 10),
        )


def test_issue_loan_unknown_reader(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(ReaderNotFound):
        usecase.run(
            reader_id=999,
            book_id=book.id,
            inventory_number='INV-1',
            on=date(2026, 3, 10),
        )


def test_issue_loan_unknown_book(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    reader_factory,
) -> None:
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    with pytest.raises(BookNotFound):
        usecase.run(
            reader_id=reader.id,
            book_id=999,
            inventory_number='INV-1',
            on=date(2026, 3, 10),
        )


def test_issue_loan_returns_loan_instance(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    book_factory,
    reader_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = _issue_loan(
        in_memory_books_repo,
        in_memory_readers_repo,
        in_memory_loans_repo,
    )
    loan = usecase.run(
        reader_id=reader.id,
        book_id=book.id,
        inventory_number='INV-1',
        on=date(2026, 3, 10),
    )
    assert isinstance(loan, Loan)
