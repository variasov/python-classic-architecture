import logging
from collections.abc import Callable

import pytest

from library.app.commands.domain.book import Book, BookIsbnInvalid, BooksRepo
from library.app.commands.use_cases.books.create_book import (
    CreateBook,
    CreateBookParams,
)
from library.app.roles import Account, PermissionDenied


@pytest.fixture
def books_repo(in_memory_books_repo: BooksRepo) -> BooksRepo:
    return in_memory_books_repo


@pytest.fixture
def create_book(books_repo: BooksRepo) -> CreateBook:
    return CreateBook(books=books_repo, logger=logging.getLogger('test'))


def test_creates_book(
    create_book: CreateBook,
    books_repo: BooksRepo,
    admin: Account,
    create_book_params: Callable[..., CreateBookParams],
) -> None:
    book_id = create_book.run(create_book_params(), admin)

    saved = books_repo.get_by_id(book_id)
    assert saved.title == 'Война и мир'
    assert saved.authors == ['Лев Толстой']


def test_requires_permission(
    create_book: CreateBook,
    books_repo: BooksRepo,
    no_books_permission: Account,
    create_book_params: Callable[..., CreateBookParams],
) -> None:
    with pytest.raises(PermissionDenied):
        create_book.run(create_book_params(), no_books_permission)

    assert books_repo.find(Book.written_by(author='Лев Толстой')) == []


def test_domain_invariant_is_checked(
    create_book: CreateBook,
    admin: Account,
    create_book_params: Callable[..., CreateBookParams],
) -> None:
    with pytest.raises(BookIsbnInvalid):
        create_book.run(create_book_params(isbn='978517118366X'), admin)


def test_params_require_authors(
    create_book_params: Callable[..., CreateBookParams],
) -> None:
    with pytest.raises(ValueError):
        create_book_params(authors=[])


def test_params_require_isbn_length(
    create_book_params: Callable[..., CreateBookParams],
) -> None:
    with pytest.raises(ValueError):
        create_book_params(isbn='123456789012')
    create_book_params(isbn='1234567890123')
