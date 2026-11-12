from collections.abc import Callable
from typing import Any

import pytest

from library.app.commands.domain.book import Book, BooksRepo
from library.app.commands.use_cases.books.create_book_from_catalog import (
    BookNotInCatalog,
    CatalogBook,
    CreateBookFromCatalog,
    CreateBookFromCatalogParams,
)
from library.app.roles import Account, PermissionDenied

ISBN = '9785171183660'


def test_creates_book_from_catalog(
    create_book_from_catalog: CreateBookFromCatalog,
    books_repo: BooksRepo,
    isbn_catalog: Any,
    admin: Account,
    create_book_from_catalog_params: Callable[
        ...,
        CreateBookFromCatalogParams,
    ],
) -> None:
    isbn_catalog.books[ISBN] = CatalogBook(
        isbn=ISBN,
        title='Война и мир',
        authors=['Лев Толстой'],
        year=1869,
    )

    created = create_book_from_catalog.run(
        create_book_from_catalog_params(isbn=ISBN),
        admin,
    )

    saved = books_repo.get_by_id(created.id)
    assert saved.isbn == ISBN
    assert saved.title == 'Война и мир'
    assert saved.authors == ['Лев Толстой']
    assert saved.published_year == 1869


def test_unknown_isbn_is_reported(
    create_book_from_catalog: CreateBookFromCatalog,
    books_repo: BooksRepo,
    admin: Account,
    create_book_from_catalog_params: Callable[
        ...,
        CreateBookFromCatalogParams,
    ],
) -> None:
    with pytest.raises(BookNotInCatalog):
        create_book_from_catalog.run(
            create_book_from_catalog_params(isbn=ISBN),
            admin,
        )

    assert books_repo.find(Book.written_by('Лев Толстой')) == []


def test_requires_permission(
    create_book_from_catalog: CreateBookFromCatalog,
    books_repo: BooksRepo,
    isbn_catalog: Any,
    no_books_permission: Account,
    create_book_from_catalog_params: Callable[
        ...,
        CreateBookFromCatalogParams,
    ],
) -> None:
    isbn_catalog.books[ISBN] = CatalogBook(
        isbn=ISBN,
        title='Война и мир',
        authors=['Лев Толстой'],
        year=1869,
    )

    with pytest.raises(PermissionDenied):
        create_book_from_catalog.run(
            create_book_from_catalog_params(isbn=ISBN),
            no_books_permission,
        )

    assert books_repo.find(Book.written_by('Лев Толстой')) == []


def test_params_require_isbn_length(
    create_book_from_catalog_params: Callable[
        ...,
        CreateBookFromCatalogParams,
    ],
) -> None:
    with pytest.raises(ValueError):
        create_book_from_catalog_params(isbn='123456789012')
    with pytest.raises(ValueError):
        create_book_from_catalog_params(isbn='12345678901234')
    create_book_from_catalog_params(isbn='1234567890123')
