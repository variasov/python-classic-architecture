from dataclasses import dataclass
from datetime import date, timedelta

from library.app.commands.domain.book import BooksRepo
from library.app.commands.domain.errors import DomainError
from library.app.commands.domain.loan import Loan, LoanPeriod, LoansRepo
from library.app.commands.domain.reader import Reader, ReadersRepo


@dataclass
class ReaderCannotBorrow(DomainError):
    reader_id: int | None

    def __str__(self) -> str:
        return f'Читатель {self.reader_id} заблокирован или членство истекло'


@dataclass
class LoanLimitExceeded(DomainError):
    reader_id: int | None
    limit: int

    def __str__(self) -> str:
        return f'Читатель {self.reader_id} уже взял максимум книг: {self.limit}'


@dataclass
class ReaderHasOverdueLoans(DomainError):
    reader_id: int | None

    def __str__(self) -> str:
        return f'У читателя {self.reader_id} есть просроченные выдачи'


class IssueLoan:
    """Выдача затрагивает три агрегата: читателя, книгу и новую выдачу."""

    def __init__(
        self,
        readers: ReadersRepo,
        books: BooksRepo,
        loans: LoansRepo,
    ) -> None:
        self.readers = readers
        self.books = books
        self.loans = loans

    def run(
        self,
        reader_id: int,
        book_id: int,
        inventory_number: str,
        on: date,
        days: int,
    ) -> Loan:
        reader = self.readers.get_by_id(reader_id)
        book = self.books.get_by_id(book_id)
        self._ensure_reader_can_borrow(reader_id, reader, on)
        book.take_copy(inventory_number)
        loan = Loan(
            reader_id=reader_id,
            book_id=book_id,
            inventory_number=inventory_number,
            issued_at=on,
            period=LoanPeriod(start=on, due=on + timedelta(days=days)),
        )
        self.books.save(book)
        return self.loans.save(loan)

    def _ensure_reader_can_borrow(
        self,
        reader_id: int,
        reader: Reader,
        on: date,
    ) -> None:
        can_borrow = Reader.membership_active(on=on) & Reader.not_blocked()
        if not can_borrow.is_satisfied_by(reader):
            raise ReaderCannotBorrow(reader_id=reader_id)
        active = self.loans.find(~Loan.returned() & Loan.of_reader(reader_id))
        limit = reader.membership.loan_limit
        if len(active) >= limit:
            raise LoanLimitExceeded(reader_id=reader_id, limit=limit)
        if any(loan.overdue(on=on) for loan in active):
            raise ReaderHasOverdueLoans(reader_id=reader_id)
