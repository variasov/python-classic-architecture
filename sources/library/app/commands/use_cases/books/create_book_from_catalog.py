import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from library.app.clock import Clock
from library.app.commands.domain.book import Book, BooksRepo
from library.app.errors import AppError
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class CatalogBook:
    """Книга во внешнем каталоге."""

    isbn: str
    title: str
    authors: list[str]
    year: int


class IsbnCatalog(ABC):
    @abstractmethod
    def find(self, isbn: str) -> CatalogBook | None: ...


@dataclass
class BookNotInCatalog(AppError):
    isbn: str

    def __str__(self) -> str:
        return f'Книги с ISBN {self.isbn} нет во внешнем каталоге'


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

    def run(self, params: CreateBookFromCatalogParams, account: Account) -> int:
        account.ensure(Permissions.BOOKS_EDIT)
        found = self.catalog.find(params.isbn)
        if found is None:
            raise BookNotInCatalog(isbn=params.isbn)
        book = Book(
            isbn=found.isbn,
            title=found.title,
            authors=list(found.authors),
            published_year=found.year,
        )
        book.check_published(self.clock.today())
        book = self.books.save(book)
        self.logger.info('Создана книга %s из каталога', book.id)
        assert book.id is not None  # noqa: S101 - save выдаёт id
        return book.id
