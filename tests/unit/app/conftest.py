from datetime import date
from typing import Any

import pytest
from classic.signals import Hub

from library.app.commands.isbn_catalog import CatalogBook, IsbnCatalog
from library.app.commands.signals import LoanIssued
from library.app.commands.use_cases.books.add_copy import AddCopyParams
from library.app.commands.use_cases.books.create_book import CreateBookParams
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalogParams,
)
from library.app.commands.use_cases.loans.extend_loan import ExtendLoanParams
from library.app.commands.use_cases.loans.issue_loan import (
    IssueLoanCommandParams,
)
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    NotificationsGateway,
    RemindOverdueLoansParams,
)
from library.app.commands.use_cases.loans.return_loan import (
    ReturnLoanCommandParams,
)
from library.app.commands.use_cases.readers.block_reader import (
    BlockReaderParams,
)
from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembershipParams,
)
from library.app.commands.use_cases.readers.register_reader import (
    RegisterReaderParams,
)
from library.app.queries.books.find_books import (
    BookDTO,
    FindBooksGateway,
    FindBooksParams,
)
from library.app.queries.books.get_book import GetBookDTO, GetBookGateway
from library.app.queries.loans.find_loans import (
    FindLoansGateway,
    FindLoansParams,
    LoanDTO,
)
from library.app.queries.readers.find_readers import (
    FindReadersGateway,
    ReaderDTO,
)
from library.app.roles import Account, Permissions

ALL_PERMISSIONS = frozenset(
    {
        Permissions.BOOKS_EDIT,
        Permissions.READERS_EDIT,
        Permissions.LOANS_EDIT,
    },
)


class FakeIsbnCatalog(IsbnCatalog):
    def __init__(self) -> None:
        self.books: dict[str, CatalogBook] = {}

    def find(self, isbn: str) -> CatalogBook | None:
        return self.books.get(isbn)


class FakeFindBooksGateway(FindBooksGateway):
    def __init__(self) -> None:
        self.calls: list[FindBooksParams] = []
        self.result: list[BookDTO] = []

    def find(self, params: FindBooksParams) -> list[BookDTO]:
        self.calls.append(params)
        return self.result


class FakeGetBookGateway(GetBookGateway):
    def __init__(self) -> None:
        self.result: GetBookDTO | None = None
        self.calls: list[int] = []

    def get(self, id: int) -> GetBookDTO | None:
        self.calls.append(id)
        return self.result


class FakeFindReadersGateway(FindReadersGateway):
    def __init__(self) -> None:
        self.result: list[ReaderDTO] = []
        self.calls: list[date] = []

    def find(self, on: date) -> list[ReaderDTO]:
        self.calls.append(on)
        return self.result


class FakeFindLoansGateway(FindLoansGateway):
    def __init__(self) -> None:
        self.result: list[LoanDTO] = []
        self.calls: list[tuple[FindLoansParams, date]] = []

    def find(
        self,
        params: FindLoansParams,
        on: date,
    ) -> list[LoanDTO]:
        self.calls.append((params, on))
        return self.result


class FakeNotificationsGateway(NotificationsGateway):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, message: str) -> None:
        self.messages.append(message)


class SignalCollector:
    def __init__(self) -> None:
        self.signals: list[Any] = []

    def __call__(self, signal: Any) -> None:
        self.signals.append(signal)


@pytest.fixture
def account() -> Account:
    return Account(login='admin', permissions=ALL_PERMISSIONS)


@pytest.fixture
def hub() -> Hub:
    return Hub()


@pytest.fixture
def isbn_catalog() -> FakeIsbnCatalog:
    return FakeIsbnCatalog()


@pytest.fixture
def find_books_gateway() -> FakeFindBooksGateway:
    return FakeFindBooksGateway()


@pytest.fixture
def get_book_gateway() -> FakeGetBookGateway:
    return FakeGetBookGateway()


@pytest.fixture
def find_readers_gateway() -> FakeFindReadersGateway:
    return FakeFindReadersGateway()


@pytest.fixture
def find_loans_gateway() -> FakeFindLoansGateway:
    return FakeFindLoansGateway()


@pytest.fixture
def notifications_gateway() -> FakeNotificationsGateway:
    return FakeNotificationsGateway()


def make_create_book_params(**overrides: Any) -> CreateBookParams:
    values: dict[str, Any] = {
        'isbn': '9780132350884',
        'title': 'Clean Code',
        'authors': ['Robert Martin'],
        'published_year': 2008,
    }
    values.update(overrides)
    return CreateBookParams(**values)


def make_create_book_from_catalog_params(
    **overrides: Any,
) -> CreateBookFromCatalogParams:
    values: dict[str, Any] = {'isbn': '9780132350884'}
    values.update(overrides)
    return CreateBookFromCatalogParams(**values)


def make_add_copy_params(**overrides: Any) -> AddCopyParams:
    values: dict[str, Any] = {
        'book_id': 1,
        'inventory_number': 'INV-2',
        'hall': 'B',
        'rack': 2,
        'shelf': 3,
    }
    values.update(overrides)
    return AddCopyParams(**values)


def make_register_reader_params(**overrides: Any) -> RegisterReaderParams:
    values: dict[str, Any] = {
        'full_name': 'Иван Иванов',
        'email': 'ivan@example.com',
        'valid_until': date(2027, 1, 1),
        'phone': None,
        'tier': 'basic',
    }
    values.update(overrides)
    return RegisterReaderParams(**values)


def make_extend_membership_params(**overrides: Any) -> ExtendMembershipParams:
    values: dict[str, Any] = {
        'reader_id': 1,
        'until': date(2028, 1, 1),
    }
    values.update(overrides)
    return ExtendMembershipParams(**values)


def make_block_reader_params(**overrides: Any) -> BlockReaderParams:
    values: dict[str, Any] = {'reader_id': 1}
    values.update(overrides)
    return BlockReaderParams(**values)


def make_issue_loan_params(**overrides: Any) -> IssueLoanCommandParams:
    values: dict[str, Any] = {
        'reader_id': 1,
        'book_id': 1,
        'inventory_number': 'INV-1',
    }
    values.update(overrides)
    return IssueLoanCommandParams(**values)


def make_extend_loan_params(**overrides: Any) -> ExtendLoanParams:
    values: dict[str, Any] = {'loan_id': 1, 'days': 7}
    values.update(overrides)
    return ExtendLoanParams(**values)


def make_return_loan_params(**overrides: Any) -> ReturnLoanCommandParams:
    values: dict[str, Any] = {'loan_id': 1}
    values.update(overrides)
    return ReturnLoanCommandParams(**values)


def make_remind_overdue_loans_params(
    **overrides: Any,
) -> RemindOverdueLoansParams:
    values: dict[str, Any] = {'on': date(2026, 3, 10)}
    values.update(overrides)
    return RemindOverdueLoansParams(**values)


def make_find_books_params(**overrides: Any) -> FindBooksParams:
    values: dict[str, Any] = {}
    values.update(overrides)
    return FindBooksParams(**values)


def make_loan_issued_signal(**overrides: Any) -> LoanIssued:
    values: dict[str, Any] = {'loan_id': 1, 'reader_id': 1}
    values.update(overrides)
    return LoanIssued(**values)


@pytest.fixture
def create_book_params_factory() -> Any:
    return make_create_book_params


@pytest.fixture
def create_book_from_catalog_params_factory() -> Any:
    return make_create_book_from_catalog_params


@pytest.fixture
def add_copy_params_factory() -> Any:
    return make_add_copy_params


@pytest.fixture
def register_reader_params_factory() -> Any:
    return make_register_reader_params


@pytest.fixture
def extend_membership_params_factory() -> Any:
    return make_extend_membership_params


@pytest.fixture
def block_reader_params_factory() -> Any:
    return make_block_reader_params


@pytest.fixture
def issue_loan_params_factory() -> Any:
    return make_issue_loan_params


@pytest.fixture
def extend_loan_params_factory() -> Any:
    return make_extend_loan_params


@pytest.fixture
def return_loan_params_factory() -> Any:
    return make_return_loan_params


@pytest.fixture
def remind_overdue_loans_params_factory() -> Any:
    return make_remind_overdue_loans_params


@pytest.fixture
def find_books_params_factory() -> Any:
    return make_find_books_params


@pytest.fixture
def loan_issued_signal_factory() -> Any:
    return make_loan_issued_signal
