import logging
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.book import Book, BookNotInCatalog, BooksRepo
from library.app.commands.isbn_catalog import IsbnCatalog
from library.app.commands.saved import saved_id
from library.app.roles import Account, PermissionDenied, Permissions


@dataclass(frozen=True)
class CreateBookFromCatalogParams:
    isbn: str


class CreateBookFromCatalog:
    def __init__(
        self,
        books: BooksRepo,
        catalog: IsbnCatalog,
        clock: Clock,
        logger: logging.Logger,
    ) -> None:
        self.books = books
        self.catalog = catalog
        self.clock = clock
        self.logger = logger

    def run(self, account: Account, params: CreateBookFromCatalogParams) -> int:
        if not account.can(Permissions.BOOKS_EDIT):
            raise PermissionDenied(
                login=account.login,
                permission=Permissions.BOOKS_EDIT,
            )
        catalog_book = self.catalog.find(params.isbn)
        if catalog_book is None:
            raise BookNotInCatalog(isbn=params.isbn)
        book = Book(
            isbn=catalog_book.isbn,
            title=catalog_book.title,
            authors=catalog_book.authors,
            published_year=catalog_book.year,
        )
        book.check(current_year=self.clock.today().year)
        saved = self.books.save(book)
        self.logger.info('Создана книга из каталога %r', saved.isbn)
        return saved_id(saved.id)
