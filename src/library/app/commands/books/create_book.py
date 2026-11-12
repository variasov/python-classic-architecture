import logging
from dataclasses import dataclass

from library.app.domain.book import Book, BooksRepo
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class CreateBookParams:
    """Параметры создания книги."""

    isbn: str
    title: str
    authors: list[str]
    published_year: int

    def __post_init__(self) -> None:
        if not self.authors:
            raise ValueError('Список авторов не может быть пустым')
        if len(self.isbn) != 13:
            raise ValueError('ISBN должен состоять из 13 символов')


@dataclass(frozen=True)
class BookCreated:
    """Контракт ответа на создание книги."""

    id: int


class CreateBook:
    """Создание книги."""

    def __init__(self, books: BooksRepo, logger: logging.Logger) -> None:
        self._books = books
        self._logger = logger

    def run(self, params: CreateBookParams, account: Account) -> BookCreated:
        account.require(Permissions.BOOKS_EDIT)
        book = Book(
            isbn=params.isbn,
            title=params.title,
            authors=list(params.authors),
            published_year=params.published_year,
        )
        saved = self._books.save(book)
        assert saved.id is not None
        self._logger.info('Книга создана: id=%s', saved.id)
        return BookCreated(id=saved.id)
