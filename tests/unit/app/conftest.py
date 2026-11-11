import logging
from collections.abc import Callable

import pytest

from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.create_book import CreateBook, CreateBookParams
from library.app.roles import Account, Permissions


@pytest.fixture
def books_repo(in_memory_books_repo: BooksRepo) -> BooksRepo:
    return in_memory_books_repo


@pytest.fixture
def create_book(books_repo: BooksRepo) -> CreateBook:
    return CreateBook(books=books_repo, logger=logging.getLogger('test'))


@pytest.fixture
def admin() -> Account:
    return Account(
        login='admin',
        permissions=(Permissions.BOOKS_EDIT, Permissions.READERS_EDIT),
    )


@pytest.fixture
def no_books_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.READERS_EDIT,))


@pytest.fixture
def create_book_params() -> Callable[..., CreateBookParams]:
    def factory(**overrides: object) -> CreateBookParams:
        fields: dict[str, object] = {
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Лев Толстой'],
            'published_year': 1869,
        }
        fields.update(overrides)
        return CreateBookParams(**fields)  # type: ignore[arg-type]

    return factory
