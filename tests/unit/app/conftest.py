import logging
from collections.abc import Callable
from datetime import date

import pytest

from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.create_book import CreateBook, CreateBookParams
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CatalogBook,
    CreateBookFromCatalog,
    CreateBookFromCatalogParams,
    IsbnCatalog,
)
from library.app.queries.books.find_books import (
    BookListItemDTO,
    FindBooks,
    FindBooksGateway,
    FindBooksParams,
)
from library.app.queries.books.get_book import (
    BookCardDTO,
    BookCopyDTO,
    GetBook,
    GetBookGateway,
    GetBookParams,
)
from library.app.queries.loans.find_loans import (
    FindLoans,
    FindLoansGateway,
    FindLoansParams,
    LoanListItemDTO,
)
from library.app.queries.readers.find_readers import (
    FindReaders,
    FindReadersGateway,
    FindReadersParams,
    ReaderListItemDTO,
)
from library.app.roles import Account, Permissions


class FakeGetBookGateway(GetBookGateway):
    """Гейтвей карточки книги: отдаёт подготовленный DTO"""

    def __init__(self, card: BookCardDTO | None = None) -> None:
        self.card = card
        self.calls: list[GetBookParams] = []

    def run(self, params: GetBookParams) -> BookCardDTO | None:
        self.calls.append(params)
        return self.card


class FakeFindBooksGateway(FindBooksGateway):
    """Гейтвей поиска книг: отдаёт подготовленный список DTO"""

    def __init__(self, books: list[BookListItemDTO] | None = None) -> None:
        self.books = books or []
        self.calls: list[FindBooksParams] = []

    def run(self, params: FindBooksParams) -> list[BookListItemDTO]:
        self.calls.append(params)
        return self.books


class FakeFindLoansGateway(FindLoansGateway):
    """Гейтвей списка выдач: отдаёт подготовленный список DTO"""

    def __init__(self, loans: list[LoanListItemDTO] | None = None) -> None:
        self.loans = loans or []
        self.calls: list[tuple[FindLoansParams, date]] = []

    def run(
        self, params: FindLoansParams, on: date
    ) -> list[LoanListItemDTO]:
        self.calls.append((params, on))
        return self.loans


class FakeFindReadersGateway(FindReadersGateway):
    """Гейтвей списка читателей: отдаёт подготовленный список DTO"""

    def __init__(self, readers: list[ReaderListItemDTO] | None = None) -> None:
        self.readers = readers or []
        self.calls: list[tuple[FindReadersParams, date]] = []

    def run(
        self, params: FindReadersParams, on: date
    ) -> list[ReaderListItemDTO]:
        self.calls.append((params, on))
        return self.readers


class FakeIsbnCatalog(IsbnCatalog):
    """Каталог ISBN: отдаёт книги из подготовленного словаря"""

    def __init__(self, books: dict[str, CatalogBook] | None = None) -> None:
        self.books = books or {}

    def find(self, isbn: str) -> CatalogBook | None:
        return self.books.get(isbn)


@pytest.fixture
def books_repo(in_memory_books_repo: BooksRepo) -> BooksRepo:
    return in_memory_books_repo


@pytest.fixture
def create_book(books_repo: BooksRepo) -> CreateBook:
    return CreateBook(books=books_repo, logger=logging.getLogger('test'))


@pytest.fixture
def isbn_catalog() -> FakeIsbnCatalog:
    return FakeIsbnCatalog()


@pytest.fixture
def create_book_from_catalog(
    books_repo: BooksRepo, isbn_catalog: FakeIsbnCatalog
) -> CreateBookFromCatalog:
    return CreateBookFromCatalog(
        books=books_repo, catalog=isbn_catalog, logger=logging.getLogger('test')
    )


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


@pytest.fixture
def create_book_from_catalog_params() -> Callable[
    ..., CreateBookFromCatalogParams
]:
    def factory(**overrides: object) -> CreateBookFromCatalogParams:
        fields: dict[str, object] = {'isbn': '9785171183660'}
        fields.update(overrides)
        return CreateBookFromCatalogParams(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def get_book_gateway() -> FakeGetBookGateway:
    return FakeGetBookGateway()


@pytest.fixture
def get_book(get_book_gateway: FakeGetBookGateway) -> GetBook:
    return GetBook(gateway=get_book_gateway)


@pytest.fixture
def find_books_gateway() -> FakeFindBooksGateway:
    return FakeFindBooksGateway()


@pytest.fixture
def find_books(find_books_gateway: FakeFindBooksGateway) -> FindBooks:
    return FindBooks(gateway=find_books_gateway)


@pytest.fixture
def find_loans_gateway() -> FakeFindLoansGateway:
    return FakeFindLoansGateway()


@pytest.fixture
def find_loans(find_loans_gateway: FakeFindLoansGateway) -> FindLoans:
    return FindLoans(gateway=find_loans_gateway)


@pytest.fixture
def find_readers_gateway() -> FakeFindReadersGateway:
    return FakeFindReadersGateway()


@pytest.fixture
def find_readers(find_readers_gateway: FakeFindReadersGateway) -> FindReaders:
    return FindReaders(gateway=find_readers_gateway)


@pytest.fixture
def book_copy_factory() -> Callable[..., BookCopyDTO]:
    def factory(**overrides: object) -> BookCopyDTO:
        fields: dict[str, object] = {
            'id': 1,
            'inventory_number': 'INV-001',
            'hall': 'Читальный зал',
            'rack': 1,
            'shelf': 1,
            'is_available': True,
        }
        fields.update(overrides)
        return BookCopyDTO(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def book_card_factory(
    book_copy_factory: Callable[..., BookCopyDTO],
) -> Callable[..., BookCardDTO]:
    def factory(**overrides: object) -> BookCardDTO:
        fields: dict[str, object] = {
            'id': 1,
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Лев Толстой'],
            'published_year': 1869,
            'copies': [book_copy_factory()],
        }
        fields.update(overrides)
        return BookCardDTO(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def book_list_item_factory() -> Callable[..., BookListItemDTO]:
    def factory(**overrides: object) -> BookListItemDTO:
        fields: dict[str, object] = {
            'id': 1,
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Лев Толстой'],
            'published_year': 1869,
            'available_copies': 1,
        }
        fields.update(overrides)
        return BookListItemDTO(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def reader_list_item_factory() -> Callable[..., ReaderListItemDTO]:
    def factory(**overrides: object) -> ReaderListItemDTO:
        fields: dict[str, object] = {
            'id': 1,
            'full_name': 'Иван Петров',
            'email': 'ivan@example.com',
            'active_loans': 0,
            'overdue_loans': 0,
        }
        fields.update(overrides)
        return ReaderListItemDTO(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def loan_list_item_factory() -> Callable[..., LoanListItemDTO]:
    def factory(**overrides: object) -> LoanListItemDTO:
        fields: dict[str, object] = {
            'id': 1,
            'reader_id': 1,
            'copy_id': 1,
            'start': date(2026, 3, 1),
            'due': date(2026, 3, 15),
            'returned_at': None,
            'extensions_count': 0,
        }
        fields.update(overrides)
        return LoanListItemDTO(**fields)  # type: ignore[arg-type]

    return factory
