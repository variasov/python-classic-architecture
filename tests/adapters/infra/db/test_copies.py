from collections.abc import Callable
from typing import Any

import pytest
from classic.criteria import Criteria, ReturnsTrue

from library.app.domain.book import Book
from library.app.domain.copy import (
    CopiesRepo,
    Copy,
    CopyNotFound,
    InventoryNumberEmpty,
)
from library.infra.db.repos.books import DbBooksRepo
from library.infra.db.repos.copies import DbCopiesRepo


@pytest.fixture(params=['db', 'in_memory'])
def copies_env(
    request: pytest.FixtureRequest,
    db_engine: Any,
    db_books_repo: DbBooksRepo,
    book_factory: Callable[..., Book],
) -> tuple[CopiesRepo, int, int]:
    """Репозиторий экземпляров и id двух существующих книг"""
    if request.param == 'db':
        repo = DbCopiesRepo(db_engine)
        book = db_books_repo.save(book_factory())
        other_book = db_books_repo.save(book_factory())
        assert book.id is not None
        assert other_book.id is not None
        return repo, book.id, other_book.id
    in_memory: CopiesRepo = request.getfixturevalue('in_memory_copies_repo')
    return in_memory, 1, 2


@pytest.fixture
def seeded_copies(
    copies_env: tuple[CopiesRepo, int, int],
    copy_factory: Callable[..., Copy],
) -> list[Copy]:
    repo, book_id, other_book_id = copies_env
    return [
        repo.save(copy_factory(book_id=book_id, inventory_number='INV-1')),
        repo.save(copy_factory(book_id=book_id, inventory_number='INV-2')),
        repo.save(copy_factory(book_id=other_book_id, inventory_number='INV-3')),
    ]


def _load(repo: CopiesRepo, copy: Copy) -> Copy:
    assert copy.id is not None
    return repo.get_by_id(copy.id)


def test_saved_copy_is_read_back(
    copies_env: tuple[CopiesRepo, int, int],
    copy_factory: Callable[..., Copy],
) -> None:
    repo, book_id, _ = copies_env
    copy = repo.save(copy_factory(book_id=book_id))

    loaded = _load(repo, copy)

    assert loaded == copy


def test_update_changes_availability(
    copies_env: tuple[CopiesRepo, int, int],
    copy_factory: Callable[..., Copy],
) -> None:
    repo, book_id, _ = copies_env
    copy = repo.save(copy_factory(book_id=book_id))
    copy.take()
    repo.save(copy)

    assert _load(repo, copy).is_available is False


def test_get_missing_copy_raises(copies_env: tuple[CopiesRepo, int, int]) -> None:
    repo, _, _ = copies_env

    with pytest.raises(CopyNotFound):
        repo.get_by_id(987654)


def test_save_invalid_copy_writes_nothing(
    copies_env: tuple[CopiesRepo, int, int],
    copy_factory: Callable[..., Copy],
) -> None:
    repo, book_id, _ = copies_env

    with pytest.raises(InventoryNumberEmpty):
        repo.save(copy_factory(book_id=book_id, inventory_number=' '))

    assert repo.find(Copy.of_book(book_id=book_id)) == []


def _criteria_for_book(book_id: int, other_book_id: int) -> dict[str, Criteria[Copy]]:
    return {
        'available': Copy.available(),
        'of_book': Copy.of_book(book_id=book_id),
        'with_inventory_number': Copy.with_inventory_number(
            inventory_number='INV-2',
        ),
        'available_and_of_book': Copy.available() & Copy.of_book(book_id=book_id),
        'available_or_other_book': Copy.available()
        | Copy.of_book(book_id=other_book_id),
        'not_of_book': ~Copy.of_book(book_id=book_id),
    }


@pytest.mark.parametrize(
    'criteria_name',
    [
        'available',
        'of_book',
        'with_inventory_number',
        'available_and_of_book',
        'available_or_other_book',
        'not_of_book',
    ],
)
def test_criteria_sql_matches_domain(
    copies_env: tuple[CopiesRepo, int, int],
    seeded_copies: list[Copy],
    criteria_name: str,
) -> None:
    repo, book_id, other_book_id = copies_env
    criteria = _criteria_for_book(book_id, other_book_id)[criteria_name]

    found = repo.find(criteria)
    expected = [copy for copy in seeded_copies if criteria.is_satisfied_by(copy)]

    assert [copy.id for copy in found] == [copy.id for copy in expected]


def test_find_returns_all_without_filters(
    copies_env: tuple[CopiesRepo, int, int],
    seeded_copies: list[Copy],
) -> None:
    repo, _, _ = copies_env

    assert len(repo.find(ReturnsTrue())) == len(seeded_copies)
