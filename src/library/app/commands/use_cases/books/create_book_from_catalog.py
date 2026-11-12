import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from library.app.commands.domain.book import Book, BooksRepo
from library.app.errors import AppError
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class CatalogBook:
    """Книга, найденная во внешнем каталоге ISBN."""

    isbn: str
    title: str
    authors: list[str]
    year: int


class IsbnCatalog(ABC):
    """Внешний каталог книг по ISBN."""

    @abstractmethod
    def find(self, isbn: str) -> CatalogBook | None: ...


@dataclass(frozen=True)
class CreateBookFromCatalogParams:
    """Параметры создания книги из каталога."""

    isbn: str

    def __post_init__(self) -> None:
        if len(self.isbn) != 13:
            raise ValueError('ISBN должен состоять из 13 символов')


@dataclass
class BookNotInCatalog(AppError):
    isbn: str

    def __str__(self) -> str:
        return f'Книга с ISBN {self.isbn} не найдена в каталоге'


@dataclass(frozen=True)
class CatalogBookCreated:
    """Контракт ответа на создание книги из каталога."""

    id: int


class CreateBookFromCatalog:
    """Создание книги по описанию из внешнего каталога ISBN."""

    def __init__(
        self,
        books: BooksRepo,
        catalog: IsbnCatalog,
        logger: logging.Logger,
    ) -> None:
        self._books = books
        self._catalog = catalog
        self._logger = logger

    def run(
        self, params: CreateBookFromCatalogParams, account: Account
    ) -> CatalogBookCreated:
        account.require(Permissions.BOOKS_EDIT)
        found = self._catalog.find(params.isbn)
        if found is None:
            raise BookNotInCatalog(isbn=params.isbn)
        book = Book(
            isbn=found.isbn,
            title=found.title,
            authors=list(found.authors),
            published_year=found.year,
        )
        saved = self._books.save(book)
        assert saved.id is not None
        self._logger.info('Книга создана из каталога: id=%s', saved.id)
        return CatalogBookCreated(id=saved.id)
