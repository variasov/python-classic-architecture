from collections.abc import Iterator
from copy import deepcopy
from datetime import UTC, date, datetime
from typing import Any

import psycopg
import pytest
from classic.criteria import Criteria
from classic.db_tools import Engine
from classic.migrations import MigrationsCollection, Migrator
from library.app.clock import Clock
from library.app.commands.domain.book import Book, BookNotFound, BooksRepo
from library.app.commands.domain.loan import Loan, LoanNotFound, LoansRepo
from library.app.commands.domain.reader import Reader, ReaderNotFound, ReadersRepo
from library.app.roles import Account, Permissions
from library.infra.db.constants import MIGRATIONS_DIR_PATH, SQL_DIR_PATH
from library.infra.db.settings import TestDBSettings
from psycopg import sql

TODAY = date(2026, 6, 15)
NOW = datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
ISBN = '9785171183660'
OTHER_ISBN = '9780306406157'
FULL_ACCESS = frozenset(
    {Permissions.BOOKS_EDIT, Permissions.READERS_EDIT, Permissions.LOANS_EDIT},
)


class FixedClock(Clock):
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def now(self) -> datetime:
        return self.moment


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
            deepcopy(b) for b in self._books.values() if criteria.is_satisfied_by(b)
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
            deepcopy(r) for r in self._readers.values() if criteria.is_satisfied_by(r)
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
            deepcopy(x) for x in self._loans.values() if criteria.is_satisfied_by(x)
        ]


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
def today() -> date:
    return TODAY


@pytest.fixture
def isbn() -> str:
    return ISBN


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def admin() -> Account:
    return Account(login='admin', permissions=FULL_ACCESS)


@pytest.fixture(scope='session')
def test_db_settings() -> TestDBSettings:
    return TestDBSettings()


@pytest.fixture(scope='session')
def migrated_db(test_db_settings: TestDBSettings) -> Iterator[None]:
    collection = MigrationsCollection(sources=[str(MIGRATIONS_DIR_PATH)])
    with Migrator(
        driver='psycopg',
        db_host=test_db_settings.DB_HOST,
        db_port=test_db_settings.DB_PORT,
        db_name=test_db_settings.DB_NAME,
        db_user=test_db_settings.DB_USER,
        db_pass=test_db_settings.DB_PASS,
        migration_schema=test_db_settings.MIGRATIONS_SCHEMA,
    ) as migrator:
        hooks, migrations = collection.to_apply(migrator.history())
        migrator.apply(migrations, hooks)
    yield
    with psycopg.connect(
        conninfo=test_db_settings.DB_CONN_INFO,
        autocommit=True,
    ) as conn:
        conn.execute('DROP SCHEMA IF EXISTS library CASCADE')
        conn.execute(
            sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(
                sql.Identifier(test_db_settings.MIGRATIONS_SCHEMA),
            ),
        )


@pytest.fixture(scope='session')
def db_engine(test_db_settings: TestDBSettings, migrated_db: None) -> Engine:
    return Engine(
        psycopg,
        lambda: psycopg.connect(conninfo=test_db_settings.DB_CONN_INFO),
        templates_dirs=[SQL_DIR_PATH],
    )


class RawDb:
    """Прямые SQL-проверки состояния БД."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def scalar(self, sql: str, **params: Any) -> Any:
        return self._engine.query(sql, static=True).scalar(**params)

    def execute(self, sql: str, **params: Any) -> None:
        self._engine.query(sql, static=True).execute(**params)


@pytest.fixture(scope='session')
def raw_db(db_engine: Engine) -> RawDb:
    return RawDb(db_engine)
