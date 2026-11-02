import logging
from collections.abc import Callable

import pytest
from library.app.clock import Clock
from library.app.commands.domain.book import (
    BookNotFound,
    BooksRepo,
    DuplicateInventoryNumber,
)
from library.app.commands.use_cases.books.add_copy import AddCopy, AddCopyParams
from library.app.commands.use_cases.books.create_book_from_catalog import (
    BookNotInCatalog,
    CatalogBook,
    CreateBookFromCatalog,
    CreateBookFromCatalogParams,
)
from library.app.queries.books.find_books import FindBooksParams
from library.app.queries.books.get_book import (
    BookCard,
    BookCardGateway,
    GetBook,
    GetBookNotFound,
    GetBookParams,
)
from library.app.roles import Account, PermissionDenied

from tests.unit.app.conftest import FakeIsbnCatalog


class FakeBookCardGateway(BookCardGateway):
    def __init__(self) -> None:
        self.cards: dict[int, BookCard] = {}

    def get(self, id: int) -> BookCard | None:
        return self.cards.get(id)


def make_add_copy_params(book_id: int, number: str = 'NEW') -> AddCopyParams:
    return AddCopyParams(
        book_id=book_id,
        inventory_number=number,
        hall='B',
        rack=2,
        shelf=3,
    )


@pytest.fixture
def add_copy(in_memory_books_repo: BooksRepo, logger: logging.Logger) -> AddCopy:
    return AddCopy(books=in_memory_books_repo, logger=logger)


def test_add_copy(
    add_copy: AddCopy,
    in_memory_books_repo: BooksRepo,
    add_book: Callable[..., int],
    admin: Account,
) -> None:
    book_id = add_book(copies=1)
    add_copy.run(make_add_copy_params(book_id), admin)
    copies = in_memory_books_repo.get_by_id(book_id).copies
    assert [c.inventory_number for c in copies] == ['INV-0', 'NEW']
    assert copies[1].shelf.rack == 2


def test_add_duplicate_copy(
    add_copy: AddCopy,
    add_book: Callable[..., int],
    admin: Account,
) -> None:
    book_id = add_book(copies=1)
    with pytest.raises(DuplicateInventoryNumber):
        add_copy.run(make_add_copy_params(book_id, 'INV-0'), admin)


def test_add_copy_unknown_book(add_copy: AddCopy, admin: Account) -> None:
    with pytest.raises(BookNotFound):
        add_copy.run(make_add_copy_params(404), admin)


def test_add_copy_permission_denied(
    add_copy: AddCopy,
    in_memory_books_repo: BooksRepo,
    add_book: Callable[..., int],
    guest: Account,
) -> None:
    book_id = add_book(copies=0)
    with pytest.raises(PermissionDenied):
        add_copy.run(make_add_copy_params(book_id), guest)
    assert in_memory_books_repo.get_by_id(book_id).copies == []


@pytest.fixture
def create_from_catalog(
    in_memory_books_repo: BooksRepo,
    catalog: FakeIsbnCatalog,
    clock: Clock,
    logger: logging.Logger,
) -> CreateBookFromCatalog:
    return CreateBookFromCatalog(
        books=in_memory_books_repo,
        catalog=catalog,
        clock=clock,
        logger=logger,
    )


def test_create_from_catalog(
    create_from_catalog: CreateBookFromCatalog,
    in_memory_books_repo: BooksRepo,
    catalog: FakeIsbnCatalog,
    isbn: str,
    admin: Account,
) -> None:
    catalog.books[isbn] = CatalogBook(
        isbn=isbn,
        title='Каталог',
        authors=['А'],
        year=2001,
    )
    book_id = create_from_catalog.run(CreateBookFromCatalogParams(isbn=isbn), admin)
    assert in_memory_books_repo.get_by_id(book_id).title == 'Каталог'


def test_create_from_catalog_not_found(
    create_from_catalog: CreateBookFromCatalog,
    isbn: str,
    admin: Account,
) -> None:
    with pytest.raises(BookNotInCatalog):
        create_from_catalog.run(CreateBookFromCatalogParams(isbn=isbn), admin)


def test_create_from_catalog_permission_denied(
    create_from_catalog: CreateBookFromCatalog,
    isbn: str,
    guest: Account,
) -> None:
    with pytest.raises(PermissionDenied):
        create_from_catalog.run(CreateBookFromCatalogParams(isbn=isbn), guest)


def test_get_book() -> None:
    gateway = FakeBookCardGateway()
    gateway.cards[1] = BookCard(
        id=1,
        isbn='9785171183660',
        title='T',
        authors=['A'],
        published_year=2000,
    )
    get_book = GetBook(gateway=gateway)
    assert get_book.run(GetBookParams(id=1)).title == 'T'
    with pytest.raises(GetBookNotFound):
        get_book.run(GetBookParams(id=2))


@pytest.mark.parametrize(
    ('limit', 'ok'),
    [(1, True), (100, True), (0, False), (101, False), (-1, False)],
)
def test_find_books_limit_boundary(limit: int, ok: bool) -> None:
    if ok:
        FindBooksParams(limit=limit)
    else:
        with pytest.raises(ValueError):
            FindBooksParams(limit=limit)


@pytest.mark.parametrize(('search', 'ok'), [('abc', True), ('ab', False), ('', False)])
def test_find_books_min_search_length(search: str, ok: bool) -> None:
    if ok:
        FindBooksParams(title__contains=search)
    else:
        with pytest.raises(ValueError):
            FindBooksParams(title__contains=search)


def test_find_books_offset_and_years() -> None:
    with pytest.raises(ValueError):
        FindBooksParams(offset=-1)
    with pytest.raises(ValueError):
        FindBooksParams(year_from=2000, year_to=1999)
    FindBooksParams(year_from=2000, year_to=2000)
