import logging
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from classic.signals import Hub
from library.app.commands.domain.book import Book, BooksRepo, ShelfLocation
from library.app.commands.domain.loan import Loan, LoanPeriod, LoansRepo
from library.app.commands.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReadersRepo,
)
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CatalogBook,
    IsbnCatalog,
)
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    NotificationsOutbox,
)
from library.app.roles import Account


class FakeIsbnCatalog(IsbnCatalog):
    def __init__(self) -> None:
        self.books: dict[str, CatalogBook] = {}

    def find(self, isbn: str) -> CatalogBook | None:
        return self.books.get(isbn)


class FakeOutbox(NotificationsOutbox):
    def __init__(self) -> None:
        self.messages: list[tuple[str, int, int, str]] = []

    def put(self, kind: str, reader_id: int, loan_id: int, text: str) -> None:
        self.messages.append((kind, reader_id, loan_id, text))


class SignalsCollector:
    def __init__(self, hub: Hub, *signal_types: type) -> None:
        self.received: list[Any] = []
        for signal_type in signal_types:
            hub.add_reaction(signal_type, self.received.append)


@pytest.fixture
def logger() -> logging.Logger:
    return logging.getLogger('test')


@pytest.fixture
def hub() -> Hub:
    return Hub()


@pytest.fixture
def catalog() -> FakeIsbnCatalog:
    return FakeIsbnCatalog()


@pytest.fixture
def outbox() -> FakeOutbox:
    return FakeOutbox()


@pytest.fixture
def guest() -> Account:
    return Account(login='guest', permissions=frozenset())


@pytest.fixture
def add_book(in_memory_books_repo: BooksRepo, isbn: str) -> Callable[..., int]:
    def factory(copies: int = 1, book_isbn: str | None = None) -> int:
        book = Book(
            isbn=book_isbn or isbn,
            title='Книга',
            authors=['Автор'],
            published_year=2000,
        )
        for number in range(copies):
            book.add_copy(f'INV-{number}', ShelfLocation(hall='A', rack=1, shelf=1))
        saved_id = in_memory_books_repo.save(book).id
        assert saved_id is not None
        return saved_id

    return factory


@pytest.fixture
def add_reader(in_memory_readers_repo: ReadersRepo, today: date) -> Callable[..., int]:
    def factory(tier: str = 'basic', valid_until: date | None = None) -> int:
        reader = Reader(
            full_name='Иван',
            contact=Contact(email='i@e.com'),
            membership=Membership(tier=tier, valid_until=valid_until or today),
        )
        saved_id = in_memory_readers_repo.save(reader).id
        assert saved_id is not None
        return saved_id

    return factory


@pytest.fixture
def add_loan(in_memory_loans_repo: LoansRepo, today: date) -> Callable[..., int]:
    def factory(
        reader_id: int,
        book_id: int,
        due_in_days: int = 14,
        inventory_number: str = 'INV-0',
    ) -> int:
        loan = Loan(
            reader_id=reader_id,
            book_id=book_id,
            inventory_number=inventory_number,
            issued_at=today - timedelta(days=30),
            period=LoanPeriod(
                start=today - timedelta(days=30),
                due=today + timedelta(days=due_in_days),
            ),
        )
        saved_id = in_memory_loans_repo.save(loan).id
        assert saved_id is not None
        return saved_id

    return factory
