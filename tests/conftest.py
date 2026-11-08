import logging
from collections.abc import Callable, Iterator
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any, cast

import psycopg
import pytest
from classic.criteria import Criteria
from classic.db_tools import Engine
from classic.db_tools.dbapi import Connection
from classic.migrations import MigrationsCollection, Migrator
from psycopg import sql

from library.app.clock import Clock
from library.app.commands.domain.book import (
    Book,
    BookNotFound,
    BooksRepo,
    Copy,
    ShelfLocation,
)
from library.app.commands.domain.loan import (
    Extension,
    Loan,
    LoanNotFound,
    LoanPeriod,
    LoansRepo,
)
from library.app.commands.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReaderNotFound,
    ReadersRepo,
)
from library.infra.db.constants import MIGRATIONS_DIR_PATH, SQL_DIR_PATH
from library.infra.db.settings import TestDBSettings

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)


class RawDB:
    def __init__(self, engine: Engine[Any]) -> None:
        self._engine = engine

    def scalar(self, sql: str, **params: Any) -> Any:
        return self._engine.query(sql, static=True).scalar(**params)

    def scalars(self, sql: str, **params: Any) -> list[Any]:
        rows = self._engine.query(sql, static=True).scalars(**params)
        return list(rows)

    def execute(self, sql: str, **params: Any) -> None:
        self._engine.query(sql, static=True).execute(**params)


@dataclass
class FixedClock(Clock):
    moment: datetime

    def now(self) -> datetime:
        return self.moment


def make_clock(day: date) -> FixedClock:
    return FixedClock(
        moment=datetime.combine(day, time(12), tzinfo=timezone.utc),
    )


def make_shelf_location(**overrides: Any) -> ShelfLocation:
    values: dict[str, Any] = {'hall': 'A', 'rack': 1, 'shelf': 1}
    values.update(overrides)
    return ShelfLocation(**values)


def make_copy(**overrides: Any) -> Copy:
    values: dict[str, Any] = {
        'inventory_number': 'INV-1',
        'shelf': make_shelf_location(),
        'is_available': True,
    }
    values.update(overrides)
    return Copy(**values)


def make_book(**overrides: Any) -> Book:
    values: dict[str, Any] = {
        'isbn': '9780132350884',
        'title': 'Clean Code',
        'authors': ['Robert Martin'],
        'published_year': 2008,
        'copies': [make_copy()],
    }
    values.update(overrides)
    return Book(**values)


def make_reader(**overrides: Any) -> Reader:
    values: dict[str, Any] = {
        'full_name': 'Иван Иванов',
        'contact': Contact(email='ivan@example.com', phone='+79990000000'),
        'membership': Membership(tier='basic', valid_until=date(2027, 1, 1)),
        'is_blocked': False,
    }
    values.update(overrides)
    return Reader(**values)


def make_loan(**overrides: Any) -> Loan:
    values: dict[str, Any] = {
        'reader_id': 1,
        'book_id': 1,
        'inventory_number': 'INV-1',
        'issued_at': TODAY,
        'period': LoanPeriod(start=TODAY, due=date(2026, 3, 24)),
        'returned_at': None,
        'extensions': [],
    }
    values.update(overrides)
    return Loan(**values)


class InMemoryBooksRepo(BooksRepo):
    def __init__(self) -> None:
        self._books: dict[int, Book] = {}
        self._next_id = 1

    def get_by_id(self, id: int) -> Book:
        if id not in self._books:
            raise BookNotFound(id=id)
        return deepcopy(self._books[id])

    def save(self, book: Book) -> Book:
        book.check()
        if book.id is None:
            book.id = self._next_id
            self._next_id += 1
        self._books[book.id] = deepcopy(book)
        return book

    def find(self, criteria: Criteria[Book]) -> list[Book]:
        return [
            deepcopy(book)
            for book in self._books.values()
            if criteria.is_satisfied_by(book)
        ]


class InMemoryReadersRepo(ReadersRepo):
    def __init__(self) -> None:
        self._readers: dict[int, Reader] = {}
        self._next_id = 1

    def get_by_id(self, id: int) -> Reader:
        if id not in self._readers:
            raise ReaderNotFound(id=id)
        return deepcopy(self._readers[id])

    def save(self, reader: Reader) -> Reader:
        reader.check()
        if reader.id is None:
            reader.id = self._next_id
            self._next_id += 1
        self._readers[reader.id] = deepcopy(reader)
        return reader

    def find(self, criteria: Criteria[Reader]) -> list[Reader]:
        return [
            deepcopy(reader)
            for reader in self._readers.values()
            if criteria.is_satisfied_by(reader)
        ]


class InMemoryLoansRepo(LoansRepo):
    def __init__(self) -> None:
        self._loans: dict[int, Loan] = {}
        self._next_id = 1

    def get_by_id(self, id: int) -> Loan:
        if id not in self._loans:
            raise LoanNotFound(id=id)
        return deepcopy(self._loans[id])

    def save(self, loan: Loan) -> Loan:
        loan.check()
        if loan.id is None:
            loan.id = self._next_id
            self._next_id += 1
        self._loans[loan.id] = deepcopy(loan)
        return loan

    def find(self, criteria: Criteria[Loan]) -> list[Loan]:
        return [
            deepcopy(loan)
            for loan in self._loans.values()
            if criteria.is_satisfied_by(loan)
        ]


@pytest.fixture(scope='session')
def test_db_settings() -> TestDBSettings:
    return TestDBSettings()


@pytest.fixture(scope='session')
def migrated_db(test_db_settings: TestDBSettings) -> Iterator[None]:
    connection_info = test_db_settings.DB_CONN_INFO
    with psycopg.connect(conninfo=connection_info, autocommit=True) as conn:
        conn.execute(sql.SQL('DROP SCHEMA IF EXISTS library CASCADE'))
        conn.execute(
            sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(
                sql.Identifier(test_db_settings.TEST_MIGRATIONS_SCHEMA),
            ),
        )
    collection = MigrationsCollection(sources=[str(MIGRATIONS_DIR_PATH)])
    with Migrator(
        driver='psycopg',
        db_host=test_db_settings.DB_HOST,
        db_port=test_db_settings.DB_PORT,
        db_name=test_db_settings.DB_NAME,
        db_user=test_db_settings.DB_USER,
        db_pass=test_db_settings.DB_PASS,
        migration_schema=test_db_settings.TEST_MIGRATIONS_SCHEMA,
    ) as migrator:
        hooks, migrations = collection.to_apply(migrator.history())
        migrator.apply(migrations, hooks)
    yield
    with psycopg.connect(conninfo=connection_info, autocommit=True) as conn:
        conn.execute(sql.SQL('DROP SCHEMA IF EXISTS library CASCADE'))
        conn.execute(
            sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(
                sql.Identifier(test_db_settings.TEST_MIGRATIONS_SCHEMA),
            ),
        )


@pytest.fixture(scope='session')
def db_engine(
    test_db_settings: TestDBSettings,
    migrated_db: None,
) -> Iterator[Engine[Any]]:
    factory = cast(
        Callable[[], Connection[Any]],
        lambda: psycopg.connect(
            conninfo=test_db_settings.DB_CONN_INFO,
        ),
    )
    engine: Engine[Any] = Engine(
        psycopg,
        factory,
        templates_dirs=[SQL_DIR_PATH],
    )
    yield engine
    engine.close()


@pytest.fixture
def raw_db(db_engine: Engine[Any]) -> RawDB:
    return RawDB(db_engine)


@pytest.fixture
def shelf_location_factory() -> Callable[..., ShelfLocation]:
    return make_shelf_location


@pytest.fixture
def copy_factory() -> Callable[..., Copy]:
    return make_copy


@pytest.fixture
def book_factory() -> Callable[..., Book]:
    return make_book


@pytest.fixture
def reader_factory() -> Callable[..., Reader]:
    return make_reader


@pytest.fixture
def loan_factory() -> Callable[..., Loan]:
    return make_loan


@pytest.fixture
def clock_factory() -> Callable[[date], Clock]:
    return make_clock


@pytest.fixture
def in_memory_books_repo() -> InMemoryBooksRepo:
    return InMemoryBooksRepo()


@pytest.fixture
def in_memory_readers_repo() -> InMemoryReadersRepo:
    return InMemoryReadersRepo()


@pytest.fixture
def in_memory_loans_repo() -> InMemoryLoansRepo:
    return InMemoryLoansRepo()


@pytest.fixture
def test_logger() -> logging.Logger:
    return logging.getLogger('library-tests')


__all__ = (
    'TODAY',
    'TOMORROW',
    'YESTERDAY',
    'Extension',
    'FixedClock',
    'RawDB',
    'make_book',
    'make_clock',
    'make_copy',
    'make_loan',
    'make_reader',
    'make_shelf_location',
)
