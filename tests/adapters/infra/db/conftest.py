from collections.abc import Callable, Iterator
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

import pytest
from classic.db_tools import Engine
from library.app.commands.domain.book import Book, ShelfLocation
from library.app.commands.domain.loan import Loan, LoanPeriod
from library.app.commands.domain.reader import Contact, Membership, Reader
from library.infra.db.gateways.book_card_gateway import DbBookCardGateway
from library.infra.db.gateways.books_search_gateway import DbBooksSearchGateway
from library.infra.db.gateways.loans_search_gateway import DbLoansSearchGateway
from library.infra.db.gateways.readers_search_gateway import DbReadersSearchGateway
from library.infra.db.repos.books_repo import DbBooksRepo
from library.infra.db.repos.loans_repo import DbLoansRepo
from library.infra.db.repos.notifications_outbox import DbNotificationsOutbox
from library.infra.db.repos.readers_repo import DbReadersRepo

from tests.conftest import ISBN, TODAY, RawDb


@pytest.fixture
def db_books_repo(db_engine: Engine) -> DbBooksRepo:
    return DbBooksRepo(db_engine)


@pytest.fixture
def db_readers_repo(db_engine: Engine) -> DbReadersRepo:
    return DbReadersRepo(db_engine)


@pytest.fixture
def db_loans_repo(db_engine: Engine) -> DbLoansRepo:
    return DbLoansRepo(db_engine)


@pytest.fixture
def db_notifications_outbox(db_engine: Engine) -> DbNotificationsOutbox:
    return DbNotificationsOutbox(db_engine)


@pytest.fixture
def books_search_gateway(db_engine: Engine) -> DbBooksSearchGateway:
    return DbBooksSearchGateway(db_engine)


@pytest.fixture
def book_card_gateway(db_engine: Engine) -> DbBookCardGateway:
    return DbBookCardGateway(db_engine)


@pytest.fixture
def readers_search_gateway(db_engine: Engine) -> DbReadersSearchGateway:
    return DbReadersSearchGateway(db_engine)


@pytest.fixture
def loans_search_gateway(db_engine: Engine) -> DbLoansSearchGateway:
    return DbLoansSearchGateway(db_engine)


@pytest.fixture
def marker() -> str:
    """Уникальная метка записей теста."""
    return uuid4().hex[:12]


@pytest.fixture
def book_factory(
    db_books_repo: DbBooksRepo,
    raw_db: RawDb,
    marker: str,
) -> Iterator[Callable[..., Book]]:
    created: list[int] = []

    def factory(copies: int = 0, **overrides: Any) -> Book:
        fields: dict[str, Any] = {
            'isbn': ISBN,
            'title': f'Книга {marker}',
            'authors': ['Автор'],
            'published_year': 2000,
        }
        book = Book(**{**fields, **overrides})
        for number in range(copies):
            book.add_copy(
                f'{marker}-{number}',
                ShelfLocation(hall='A', rack=1, shelf=1),
            )
        db_books_repo.save(book)
        assert book.id is not None
        created.append(book.id)
        return book

    yield factory
    raw_db.execute('DELETE FROM library.books WHERE id = ANY(%(ids)s)', ids=created)


@pytest.fixture
def reader_factory(
    db_readers_repo: DbReadersRepo,
    raw_db: RawDb,
    marker: str,
) -> Iterator[Callable[..., Reader]]:
    created: list[int] = []

    def factory(
        tier: str = 'basic',
        valid_until: date = TODAY,
        **overrides: Any,
    ) -> Reader:
        fields: dict[str, Any] = {
            'full_name': f'Читатель {marker}',
            'contact': Contact(email=f'{marker}@example.com', phone='123'),
            'membership': Membership(tier=tier, valid_until=valid_until),
        }
        reader = Reader(**{**fields, **overrides})
        db_readers_repo.save(reader)
        assert reader.id is not None
        created.append(reader.id)
        return reader

    yield factory
    raw_db.execute('DELETE FROM library.readers WHERE id = ANY(%(ids)s)', ids=created)


@pytest.fixture
def loan_factory(
    db_loans_repo: DbLoansRepo,
    book_factory: Callable[..., Book],
    reader_factory: Callable[..., Reader],
    marker: str,
) -> Callable[..., Loan]:
    """Выдачи удаляются каскадом вместе с читателем и книгой."""

    def factory(
        reader: Reader | None = None,
        book: Book | None = None,
        due_in_days: int = 14,
        **overrides: Any,
    ) -> Loan:
        reader = reader or reader_factory()
        book = book or book_factory(copies=1)
        start = TODAY - timedelta(days=30)
        fields: dict[str, Any] = {
            'reader_id': reader.id,
            'book_id': book.id,
            'inventory_number': f'{marker}-0',
            'issued_at': start,
            'period': LoanPeriod(start=start, due=TODAY + timedelta(days=due_in_days)),
        }
        loan = Loan(**{**fields, **overrides})
        db_loans_repo.save(loan)
        return loan

    return factory
