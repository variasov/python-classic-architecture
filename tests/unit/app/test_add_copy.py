import logging
from collections.abc import Callable

import pytest

from library.app.commands.domain.book import Book, BookNotFound, BooksRepo
from library.app.commands.domain.copy import Copy, CopiesRepo
from library.app.commands.use_cases.books.add_copy import (
    AddCopy,
    AddCopyParams,
    InventoryNumberTaken,
)
from library.app.roles import Account, PermissionDenied


@pytest.fixture
def add_copy_params() -> Callable[..., AddCopyParams]:
    def factory(**overrides: object) -> AddCopyParams:
        fields: dict[str, object] = {
            'book_id': 1,
            'inventory_number': 'INV-001',
            'hall': 'Читальный зал',
            'rack': 1,
            'shelf': 1,
        }
        fields.update(overrides)
        return AddCopyParams(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def books_with_one(books_repo: BooksRepo, book_factory: Callable[..., Book]) -> Book:
    return books_repo.save(book_factory())


@pytest.fixture
def add_copy(books_repo: BooksRepo, copies_repo: CopiesRepo) -> AddCopy:
    return AddCopy(
        books=books_repo, copies=copies_repo, logger=logging.getLogger('test')
    )


@pytest.fixture
def copies_repo(in_memory_copies_repo: CopiesRepo) -> CopiesRepo:
    return in_memory_copies_repo


def test_adds_copy(
    add_copy: AddCopy,
    copies_repo: CopiesRepo,
    books_with_one: Book,
    admin: Account,
    add_copy_params: Callable[..., AddCopyParams],
) -> None:
    assert books_with_one.id is not None
    copy_id = add_copy.run(
        add_copy_params(book_id=books_with_one.id), admin
    )

    saved = copies_repo.get_by_id(copy_id)
    assert saved.inventory_number == 'INV-001'
    assert saved.shelf.hall == 'Читальный зал'
    assert saved.is_available is True


def test_requires_existing_book(
    add_copy: AddCopy,
    admin: Account,
    add_copy_params: Callable[..., AddCopyParams],
) -> None:
    with pytest.raises(BookNotFound):
        add_copy.run(add_copy_params(book_id=404), admin)


def test_inventory_number_must_be_unique(
    add_copy: AddCopy,
    books_with_one: Book,
    admin: Account,
    add_copy_params: Callable[..., AddCopyParams],
) -> None:
    assert books_with_one.id is not None
    add_copy.run(add_copy_params(book_id=books_with_one.id), admin)

    with pytest.raises(InventoryNumberTaken):
        add_copy.run(add_copy_params(book_id=books_with_one.id), admin)


def test_requires_permission(
    add_copy: AddCopy,
    copies_repo: CopiesRepo,
    books_with_one: Book,
    no_books_permission: Account,
    add_copy_params: Callable[..., AddCopyParams],
) -> None:
    assert books_with_one.id is not None
    with pytest.raises(PermissionDenied):
        add_copy.run(
            add_copy_params(book_id=books_with_one.id), no_books_permission
        )

    assert copies_repo.find(Copy.available()) == []


def test_params_accept_minimal_shelf_position(
    add_copy_params: Callable[..., AddCopyParams],
) -> None:
    params = add_copy_params(rack=1, shelf=1)

    assert params.rack == 1
    assert params.shelf == 1


def test_params_require_positive_shelf(
    add_copy_params: Callable[..., AddCopyParams],
) -> None:
    with pytest.raises(ValueError):
        add_copy_params(rack=0)
    with pytest.raises(ValueError):
        add_copy_params(shelf=0)
    with pytest.raises(ValueError):
        add_copy_params(rack=-1)
    with pytest.raises(ValueError):
        add_copy_params(shelf=-1)
