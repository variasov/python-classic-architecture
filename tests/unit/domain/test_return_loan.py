from datetime import date

import pytest

from library.app.commands.domain.book import BookNotFound
from library.app.commands.domain.loan import (
    LoanAlreadyReturned,
    LoanNotFound,
    LoanPeriod,
)
from library.app.commands.domain.return_loan import ReturnLoan


def _return_loan(books_repo, loans_repo) -> ReturnLoan:
    return ReturnLoan(books=books_repo, loans=loans_repo)


def test_return_loan_success(
    in_memory_books_repo,
    in_memory_loans_repo,
    book_factory,
    copy_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(
        book_factory(copies=[copy_factory(is_available=False)]),
    )
    loan = in_memory_loans_repo.save(
        loan_factory(book_id=book.id, inventory_number='INV-1'),
    )
    usecase = _return_loan(in_memory_books_repo, in_memory_loans_repo)
    returned = usecase.run(loan_id=loan.id, on=date(2026, 3, 15))
    assert returned.returned_at == date(2026, 3, 15)
    assert in_memory_loans_repo.get_by_id(loan.id).returned_at == date(
        2026,
        3,
        15,
    )
    assert in_memory_books_repo.get_by_id(book.id).copies[0].is_available


def test_return_loan_unknown_loan(
    in_memory_books_repo,
    in_memory_loans_repo,
) -> None:
    usecase = _return_loan(in_memory_books_repo, in_memory_loans_repo)
    with pytest.raises(LoanNotFound):
        usecase.run(loan_id=999, on=date(2026, 3, 15))


def test_return_loan_unknown_book(
    in_memory_books_repo,
    in_memory_loans_repo,
    loan_factory,
) -> None:
    loan = in_memory_loans_repo.save(loan_factory(book_id=999))
    usecase = _return_loan(in_memory_books_repo, in_memory_loans_repo)
    with pytest.raises(BookNotFound):
        usecase.run(loan_id=loan.id, on=date(2026, 3, 15))


def test_return_loan_twice_is_rejected(
    in_memory_books_repo,
    in_memory_loans_repo,
    book_factory,
    copy_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(
        book_factory(copies=[copy_factory(is_available=False)]),
    )
    loan = in_memory_loans_repo.save(
        loan_factory(book_id=book.id, inventory_number='INV-1'),
    )
    usecase = _return_loan(in_memory_books_repo, in_memory_loans_repo)
    usecase.run(loan_id=loan.id, on=date(2026, 3, 15))
    with pytest.raises(LoanAlreadyReturned):
        usecase.run(loan_id=loan.id, on=date(2026, 3, 16))


def test_return_loan_period_is_unchanged(
    in_memory_books_repo,
    in_memory_loans_repo,
    book_factory,
    copy_factory,
    loan_factory,
) -> None:
    book = in_memory_books_repo.save(
        book_factory(copies=[copy_factory(is_available=False)]),
    )
    period = LoanPeriod(
        start=date(2026, 3, 10),
        due=date(2026, 3, 24),
    )
    loan = in_memory_loans_repo.save(
        loan_factory(book_id=book.id, period=period),
    )
    usecase = _return_loan(in_memory_books_repo, in_memory_loans_repo)
    returned = usecase.run(loan_id=loan.id, on=date(2026, 3, 15))
    assert returned.period == period
