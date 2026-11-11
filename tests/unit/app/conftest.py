import logging
from collections.abc import Callable

import pytest

from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.create_book import CreateBook, CreateBookParams
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


@pytest.fixture
def books_repo(in_memory_books_repo: BooksRepo) -> BooksRepo:
    return in_memory_books_repo


@pytest.fixture
def create_book(books_repo: BooksRepo) -> CreateBook:
    return CreateBook(books=books_repo, logger=logging.getLogger('test'))


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
