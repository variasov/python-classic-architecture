from collections.abc import Callable, Iterator
from typing import Any

import pytest
from classic.db_tools import Engine

from library.app.commands.domain.loan import Loan
from library.infra.db.gateways.find_books import FindBooksGatewayImpl
from library.infra.db.gateways.find_loans import FindLoansGatewayImpl
from library.infra.db.gateways.find_readers import FindReadersGatewayImpl
from library.infra.db.gateways.get_book import GetBookGatewayImpl
from library.infra.db.gateways.notifications import (
    NotificationsGatewayImpl,
)
from library.infra.db.repos.books import BooksRepository
from library.infra.db.repos.loans import LoansRepository
from library.infra.db.repos.readers import ReadersRepository


@pytest.fixture
def db_scope(db_engine: Engine[Any]) -> Iterator[None]:
    with db_engine.transaction(commit=False):
        yield


@pytest.fixture
def db_books_repo(
    db_engine: Engine[Any],
    db_scope: None,
) -> BooksRepository:
    return BooksRepository(db=db_engine)


@pytest.fixture
def db_readers_repo(
    db_engine: Engine[Any],
    db_scope: None,
) -> ReadersRepository:
    return ReadersRepository(db=db_engine)


@pytest.fixture
def db_loans_repo(
    db_engine: Engine[Any],
    db_scope: None,
) -> LoansRepository:
    return LoansRepository(db=db_engine)


@pytest.fixture
def find_books_gateway_db(
    db_engine: Engine[Any],
    db_scope: None,
) -> FindBooksGatewayImpl:
    return FindBooksGatewayImpl(db=db_engine)


@pytest.fixture
def get_book_gateway_db(
    db_engine: Engine[Any],
    db_scope: None,
) -> GetBookGatewayImpl:
    return GetBookGatewayImpl(db=db_engine)


@pytest.fixture
def find_readers_gateway_db(
    db_engine: Engine[Any],
    db_scope: None,
) -> FindReadersGatewayImpl:
    return FindReadersGatewayImpl(db=db_engine)


@pytest.fixture
def find_loans_gateway_db(
    db_engine: Engine[Any],
    db_scope: None,
) -> FindLoansGatewayImpl:
    return FindLoansGatewayImpl(db=db_engine)


@pytest.fixture
def notifications_gateway_db(
    db_engine: Engine[Any],
    db_scope: None,
) -> NotificationsGatewayImpl:
    return NotificationsGatewayImpl(db=db_engine)


@pytest.fixture(params=['db_books_repo', 'in_memory_books_repo'])
def any_books_repo(request: pytest.FixtureRequest) -> Any:
    return request.getfixturevalue(request.param)


@pytest.fixture(params=['db_readers_repo', 'in_memory_readers_repo'])
def any_readers_repo(request: pytest.FixtureRequest) -> Any:
    return request.getfixturevalue(request.param)


@pytest.fixture(params=['db_loans_repo', 'in_memory_loans_repo'])
def any_loans_repo(request: pytest.FixtureRequest) -> Any:
    return request.getfixturevalue(request.param)


@pytest.fixture
def loan_factory_with_parents(
    any_loans_repo: Any,
    request: pytest.FixtureRequest,
) -> Callable[..., Loan]:
    base: Callable[..., Loan] = request.getfixturevalue('loan_factory')
    if not isinstance(any_loans_repo, LoansRepository):
        return base
    books = request.getfixturevalue('db_books_repo')
    readers = request.getfixturevalue('db_readers_repo')
    book_factory = request.getfixturevalue('book_factory')
    reader_factory = request.getfixturevalue('reader_factory')
    book = books.save(book_factory(copies=[]))
    first = readers.save(reader_factory(full_name='Reader 1'))
    second = readers.save(reader_factory(full_name='Reader 2'))
    readers_map = {1: first.id, 2: second.id}

    def factory(**overrides: Any) -> Loan:
        values = dict(overrides)
        requested_reader = values.get('reader_id', 1)
        values['reader_id'] = readers_map.get(requested_reader, requested_reader)
        values.setdefault('book_id', book.id)
        return base(**values)

    return factory
