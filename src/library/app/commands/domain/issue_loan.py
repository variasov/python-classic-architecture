from datetime import date, timedelta
from typing import ClassVar

from library.app.commands.domain.book import BooksRepo, NoAvailableCopies
from library.app.commands.domain.loan import Loan, LoanPeriod, LoansRepo
from library.app.commands.domain.reader import (
    LoanLimitExceeded,
    Reader,
    ReaderCannotBorrow,
    ReaderHasOverdueLoans,
    ReadersRepo,
)


class IssueLoan:
    """Выдаёт экземпляр книги читателю, затрагивая три агрегата."""

    LOAN_TERM_DAYS: ClassVar[int] = 14

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
    ) -> Loan:
        reader = self.readers.get_by_id(reader_id)
        can_borrow = Reader.membership_active(on=on) & Reader.not_blocked()
        if not can_borrow.is_satisfied_by(reader):
            raise ReaderCannotBorrow(reader_id=reader_id)

        active = self.loans.find(
            ~Loan.returned() & Loan.belongs_to_reader(reader_id=reader_id),
        )
        if len(active) >= reader.membership.loan_limit:
            raise LoanLimitExceeded(
                reader_id=reader_id,
                limit=reader.membership.loan_limit,
            )

        overdue = self.loans.find(
            Loan.overdue(on=on) & Loan.belongs_to_reader(reader_id=reader_id),
        )
        if overdue:
            raise ReaderHasOverdueLoans(reader_id=reader_id)

        book = self.books.get_by_id(book_id)
        if not book.has_available_copies():
            raise NoAvailableCopies(book_id=book_id)
        book.take_copy(inventory_number)
        loan = Loan(
            reader_id=reader_id,
            book_id=book_id,
            inventory_number=inventory_number,
            issued_at=on,
            period=LoanPeriod(
                start=on,
                due=on + timedelta(days=self.LOAN_TERM_DAYS),
            ),
        )
        self.books.save(book)
        return self.loans.save(loan)
