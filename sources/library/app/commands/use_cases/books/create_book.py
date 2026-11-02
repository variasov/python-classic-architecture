import logging
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.book import Book, BooksRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class CreateBookParams:
    isbn: str
    title: str
    authors: list[str]
    published_year: int


class CreateBook:
    def __init__(self, books: BooksRepo, clock: Clock, logger: logging.Logger) -> None:
        self.books = books
        self.clock = clock
        self.logger = logger

    def run(self, params: CreateBookParams, account: Account) -> int:
        account.ensure(Permissions.BOOKS_EDIT)
        book = Book(
            isbn=params.isbn,
            title=params.title,
            authors=list(params.authors),
            published_year=params.published_year,
        )
        book.check_published(self.clock.today())
        book = self.books.save(book)
        self.logger.info('Создана книга %s', book.id)
        assert book.id is not None  # noqa: S101 - save выдаёт id
        return book.id
