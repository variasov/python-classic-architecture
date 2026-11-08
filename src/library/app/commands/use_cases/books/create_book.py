import logging
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.book import Book, BooksRepo
from library.app.commands.saved import saved_id
from library.app.roles import Account, PermissionDenied, Permissions


@dataclass(frozen=True)
class CreateBookParams:
    isbn: str
    title: str
    authors: list[str]
    published_year: int


class CreateBook:
    def __init__(
        self,
        books: BooksRepo,
        clock: Clock,
        logger: logging.Logger,
    ) -> None:
        self.books = books
        self.clock = clock
        self.logger = logger

    def run(self, account: Account, params: CreateBookParams) -> int:
        if not account.can(Permissions.BOOKS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.BOOKS_EDIT,
            )
        book = Book(
            isbn=params.isbn,
            title=params.title,
            authors=params.authors,
            published_year=params.published_year,
        )
        book.check(current_year=self.clock.today().year)
        saved = self.books.save(book)
        self.logger.info('Создана книга %r с id=%s', saved.title, saved.id)
        return saved_id(saved.id)
