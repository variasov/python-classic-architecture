from datetime import date

from library.app.commands.domain.book import BooksRepo
from library.app.commands.domain.loan import LoansRepo


class ReturnLoan:
    """Возврат затрагивает два агрегата: выдачу и книгу."""

    def __init__(self, loans: LoansRepo, books: BooksRepo) -> None:
        self.loans = loans
        self.books = books

    def run(self, loan_id: int, on: date) -> None:
        loan = self.loans.get_by_id(loan_id)
        book = self.books.get_by_id(loan.book_id)
        loan.close(on)
        book.return_copy(loan.inventory_number)
        self.loans.save(loan)
        self.books.save(book)
