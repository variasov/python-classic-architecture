import logging
from collections.abc import Callable
from typing import Any

import pytest
from library.app.clock import Clock
from library.app.commands.domain.book import (
    Book,
    BooksRepo,
    InvalidIsbn,
    PublishedInFuture,
)
from library.app.commands.use_cases.books.create_book import (
    CreateBook,
    CreateBookParams,
)
from library.app.roles import Account, PermissionDenied

EVERY_BOOK = Book.published_after(year=0) | ~Book.published_after(year=0)

MakeParams = Callable[..., CreateBookParams]


@pytest.fixture
def make_params(isbn: str) -> MakeParams:
    def factory(**overrides: Any) -> CreateBookParams:
        fields: dict[str, Any] = {
            'isbn': isbn,
            'title': 'Война и мир',
            'authors': ['Толстой'],
            'published_year': 1869,
        }
        return CreateBookParams(**{**fields, **overrides})

    return factory


@pytest.fixture
def create_book(
    in_memory_books_repo: BooksRepo,
    clock: Clock,
    logger: logging.Logger,
) -> CreateBook:
    return CreateBook(books=in_memory_books_repo, clock=clock, logger=logger)


def test_create_book(
    create_book: CreateBook,
    in_memory_books_repo: BooksRepo,
    admin: Account,
    make_params: MakeParams,
) -> None:
    book_id = create_book.run(make_params(), admin)
    assert in_memory_books_repo.get_by_id(book_id).title == 'Война и мир'


def test_published_year_boundary(
    create_book: CreateBook,
    admin: Account,
    make_params: MakeParams,
) -> None:
    create_book.run(make_params(published_year=2026), admin)
    with pytest.raises(PublishedInFuture):
        create_book.run(make_params(published_year=2027), admin)


def test_invalid_isbn(
    create_book: CreateBook,
    admin: Account,
    make_params: MakeParams,
) -> None:
    with pytest.raises(InvalidIsbn):
        create_book.run(make_params(isbn='123'), admin)


def test_permission_denied(
    create_book: CreateBook,
    in_memory_books_repo: BooksRepo,
    guest: Account,
    make_params: MakeParams,
) -> None:
    with pytest.raises(PermissionDenied):
        create_book.run(make_params(), guest)
    assert in_memory_books_repo.find(EVERY_BOOK) == []
