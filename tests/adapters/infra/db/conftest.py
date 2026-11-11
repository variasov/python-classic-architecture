from collections.abc import Callable, Iterator
from typing import Any

import pytest
from classic.db_tools import Engine

from library.app.commands.domain.book import Book, BooksRepo
from library.infra.db.repos.books import DbBooksRepo


@pytest.fixture(autouse=True)
def _rollback(db_engine: Engine[tuple[Any, ...]]) -> Iterator[None]:
    """Изоляция: изменения теста откатываются после его завершения"""
    with db_engine.transaction(commit=False):
        yield


@pytest.fixture
def db_books_repo(db_engine: Engine[tuple[Any, ...]]) -> DbBooksRepo:
    return DbBooksRepo(db_engine)


@pytest.fixture
def saved_book(
    book_factory: Callable[..., Book], db_books_repo: BooksRepo
) -> Book:
    return db_books_repo.save(book_factory())


@pytest.fixture(params=['db_books_repo', 'in_memory_books_repo'])
def any_books_repo(request: pytest.FixtureRequest) -> BooksRepo:
    repo: BooksRepo = request.getfixturevalue(request.param)
    return repo
