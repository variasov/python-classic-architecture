from collections.abc import Callable, Iterator
from typing import Any

import pytest
from classic.db_tools import Engine

from library.app.commands.domain.book import Book, BooksRepo
from library.app.queries.books.find_books import FindBooksGateway
from library.app.queries.books.get_book import GetBookGateway
from library.infra.db.gateways.find_books import DbFindBooksGateway
from library.infra.db.gateways.get_book import DbGetBookGateway
from library.infra.db.repos.books import DbBooksRepo
from library.infra.db.repos.copies import DbCopiesRepo

_DB_ENGINE = Engine[tuple[Any, ...]]


@pytest.fixture(autouse=True)
def _rollback(db_engine: _DB_ENGINE) -> Iterator[None]:
    """Изоляция: изменения теста откатываются после его завершения"""
    with db_engine.transaction(commit=False):
        yield


@pytest.fixture
def db_books_repo(db_engine: _DB_ENGINE) -> DbBooksRepo:
    return DbBooksRepo(db_engine)


@pytest.fixture
def db_copies_repo(db_engine: _DB_ENGINE) -> DbCopiesRepo:
    return DbCopiesRepo(db_engine)


@pytest.fixture
def db_get_book_gateway(db_engine: _DB_ENGINE) -> GetBookGateway:
    return DbGetBookGateway(db_engine)


@pytest.fixture
def db_find_books_gateway(db_engine: _DB_ENGINE) -> FindBooksGateway:
    return DbFindBooksGateway(db_engine)


@pytest.fixture
def saved_book(
    book_factory: Callable[..., Book], db_books_repo: BooksRepo
) -> Book:
    return db_books_repo.save(book_factory())


@pytest.fixture(params=['db_books_repo', 'in_memory_books_repo'])
def any_books_repo(request: pytest.FixtureRequest) -> BooksRepo:
    repo: BooksRepo = request.getfixturevalue(request.param)
    return repo
