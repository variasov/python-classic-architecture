import os
from collections.abc import Callable, Iterator
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast

import psycopg
import pytest
from classic.criteria import Criteria
from classic.db_tools import Engine
from classic.db_tools.dbapi import Connection
from classic.migrations import MigrationsCollection, Migrator
from dotenv import dotenv_values
from psycopg import sql

from library.app.commands.domain.book import Book, BookNotFound, BooksRepo
from library.app.commands.domain.copy import (
    Copy,
    CopyNotFound,
    CopiesRepo,
    ShelfLocation,
)
from library.app.commands.domain.loan import (
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
from library.infra.db.settings import DBSettings

_ENV_FILE = Path(__file__).parent.parent / '.env'

for _name, _value in dotenv_values(_ENV_FILE).items():
    if _value is not None:
        os.environ.setdefault(_name, _value)

os.environ.setdefault('API_HOST', '127.0.0.1')
os.environ.setdefault('API_PORT', '8080')
os.environ.setdefault('ISBN_CATALOG_URL', 'http://127.0.0.1:9/')

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)


class RawDb:
    """Прямые SQL-проверки состояния БД"""

    def __init__(self, engine: Engine[tuple[Any, ...]]) -> None:
        self._engine = engine

    def scalar(self, query: str, **params: Any) -> Any:
        return self._engine.query(query, static=True).scalar(**params)

    def scalars(self, query: str, **params: Any) -> list[Any]:
        return list(self._engine.query(query, static=True).scalars(**params))

    def execute(self, query: str, **params: Any) -> int:
        return self._engine.query(query, static=True).execute(**params).rowcount


@pytest.fixture(scope='session')
def db_settings() -> DBSettings:
    return DBSettings()  # pyright: ignore[reportCallIssue]  # значения из окружения


def _drop_schemas(settings: DBSettings) -> None:
    with psycopg.connect(conninfo=settings.DB_CONN_INFO) as connection:
        with connection.cursor() as cursor:
            for schema in ('library', settings.MIGRATIONS_SCHEMA):
                cursor.execute(
                    sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(
                        sql.Identifier(schema)
                    )
                )
        connection.commit()


@pytest.fixture(scope='session')
def migrated_db(db_settings: DBSettings) -> Iterator[DBSettings]:
    _drop_schemas(db_settings)
    collection = MigrationsCollection(sources=[str(MIGRATIONS_DIR_PATH)])
    with Migrator(
        driver='psycopg',
        db_host=db_settings.DB_HOST,
        db_port=db_settings.DB_PORT,
        db_name=db_settings.DB_NAME,
        db_user=db_settings.DB_USER,
        db_pass=db_settings.DB_PASS,
        migration_schema=db_settings.MIGRATIONS_SCHEMA,
    ) as migrator:
        hooks, migrations = collection.to_apply(migrator.history())
        migrator.apply(migrations, hooks)
    yield db_settings
    _drop_schemas(db_settings)


@pytest.fixture(scope='session')
def db_engine(migrated_db: DBSettings) -> Iterator[Engine[tuple[Any, ...]]]:
    def connect() -> Connection[tuple[Any, ...]]:
        return cast(
            'Connection[tuple[Any, ...]]',
            psycopg.connect(conninfo=migrated_db.DB_CONN_INFO),
        )

    engine: Engine[tuple[Any, ...]] = Engine(
        psycopg,
        connect,
        templates_dirs=[SQL_DIR_PATH],
    )
    yield engine
    engine.close()


@pytest.fixture
def raw_db(db_engine: Engine[tuple[Any, ...]]) -> RawDb:
    return RawDb(db_engine)


class InMemoryBooksRepo(BooksRepo):
    """In-memory реализация репозитория книг для unit- и контрактных тестов"""

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


def make_book(**overrides: Any) -> Book:
    fields: dict[str, Any] = {
        'isbn': '9785171183660',
        'title': 'Война и мир',
        'authors': ['Лев Толстой'],
        'published_year': 1869,
    }
    fields.update(overrides)
    return Book(**fields)


@pytest.fixture
def book_factory() -> Callable[..., Book]:
    return make_book


@pytest.fixture
def in_memory_books_repo() -> InMemoryBooksRepo:
    return InMemoryBooksRepo()


class InMemoryCopiesRepo(CopiesRepo):
    """In-memory реализация репозитория экземпляров"""

    def __init__(self) -> None:
        self._copies: dict[int, Copy] = {}
        self._next_id = 1

    def get_by_id(self, id: int) -> Copy:
        if id not in self._copies:
            raise CopyNotFound(id=id)
        return deepcopy(self._copies[id])

    def save(self, copy: Copy) -> Copy:
        copy.check()
        if copy.id is None:
            copy.id = self._next_id
            self._next_id += 1
        self._copies[copy.id] = deepcopy(copy)
        return copy

    def find(self, criteria: Criteria[Copy]) -> list[Copy]:
        return [
            deepcopy(copy)
            for copy in self._copies.values()
            if criteria.is_satisfied_by(copy)
        ]


def make_copy(**overrides: Any) -> Copy:
    fields: dict[str, Any] = {
        'book_id': 1,
        'inventory_number': 'INV-001',
        'shelf': ShelfLocation(hall='Читальный зал', rack=1, shelf=1),
        'is_available': True,
    }
    fields.update(overrides)
    return Copy(**fields)


@pytest.fixture
def copy_factory() -> Callable[..., Copy]:
    return make_copy


@pytest.fixture
def in_memory_copies_repo() -> InMemoryCopiesRepo:
    return InMemoryCopiesRepo()


class InMemoryReadersRepo(ReadersRepo):
    """In-memory реализация репозитория читателей"""

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


def make_reader(**overrides: Any) -> Reader:
    fields: dict[str, Any] = {
        'full_name': 'Иван Петров',
        'contact': Contact(email='ivan@example.com'),
        'membership': Membership(tier='basic', valid_until=TOMORROW),
    }
    fields.update(overrides)
    return Reader(**fields)


@pytest.fixture
def reader_factory() -> Callable[..., Reader]:
    return make_reader


@pytest.fixture
def in_memory_readers_repo() -> InMemoryReadersRepo:
    return InMemoryReadersRepo()


class InMemoryLoansRepo(LoansRepo):
    """In-memory реализация репозитория выдач"""

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


def make_loan(**overrides: Any) -> Loan:
    fields: dict[str, Any] = {
        'reader_id': 1,
        'copy_id': 1,
        'period': LoanPeriod(
            start=TODAY, due=TODAY + timedelta(days=Loan.TERM_DAYS)
        ),
    }
    fields.update(overrides)
    return Loan(**fields)


@pytest.fixture
def loan_factory() -> Callable[..., Loan]:
    return make_loan


@pytest.fixture
def in_memory_loans_repo() -> InMemoryLoansRepo:
    return InMemoryLoansRepo()
