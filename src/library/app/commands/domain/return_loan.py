from datetime import date

from library.app.commands.domain.book import BooksRepo
from library.app.commands.domain.loan import Loan, LoansRepo


class ReturnLoan:
    """Принимает экземпляр книги обратно."""

    def __init__(self, books: BooksRepo, loans: LoansRepo) -> None:
        self.books = books
        self.loans = loans

    def run(self, loan_id: int, on: date) -> Loan:
        loan = self.loans.get_by_id(loan_id)
        book = self.books.get_by_id(loan.book_id)
        loan.close(on)
        book.return_copy(loan.inventory_number)
        self.books.save(book)
        return self.loans.save(loan)
