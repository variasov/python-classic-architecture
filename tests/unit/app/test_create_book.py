from collections.abc import Callable

import pytest

from library.app.commands.books.create_book import (
    CreateBook,
    CreateBookParams,
)
from library.app.domain.book import Book, BookIsbnInvalid, BooksRepo
from library.app.roles import Account, PermissionDenied


def test_creates_book(
    create_book: CreateBook,
    books_repo: BooksRepo,
    admin: Account,
    create_book_params: Callable[..., CreateBookParams],
) -> None:
    created = create_book.run(create_book_params(), admin)

    saved = books_repo.get_by_id(created.id)
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
