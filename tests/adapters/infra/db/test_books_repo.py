from collections.abc import Callable

import pytest
from library.app.commands.domain.book import (
    Book,
    BookNotFound,
    BooksRepo,
    InvalidIsbn,
    ShelfLocation,
)
from library.infra.db.repos.books_repo import DbBooksRepo

from tests.conftest import RawDb


@pytest.fixture(params=['db_books_repo', 'in_memory_books_repo'])
def any_books_repo(request: pytest.FixtureRequest) -> BooksRepo:
    return request.getfixturevalue(request.param)


def make_book(marker: str, **overrides: object) -> Book:
    fields: dict[str, object] = {
        'isbn': '9785171183660',
        'title': f'Книга {marker}',
        'authors': ['А', 'Б'],
        'published_year': 1999,
    }
    return Book(**{**fields, **overrides})  # type: ignore[arg-type]


def test_save_and_get(any_books_repo: BooksRepo, marker: str, raw_db: RawDb) -> None:
    book = make_book(marker)
    book.add_copy('C1', ShelfLocation(hall='A', rack=2, shelf=3))
    book.add_copy('C2', ShelfLocation(hall='B', rack=1, shelf=1))
    book.take_copy('C2')
    any_books_repo.save(book)
    assert book.id is not None
    try:
        assert any_books_repo.get_by_id(book.id) == book
    finally:
        raw_db.execute('DELETE FROM library.books WHERE id = %(id)s', id=book.id)


def test_get_without_copies(
    any_books_repo: BooksRepo,
    marker: str,
    raw_db: RawDb,
) -> None:
    book = any_books_repo.save(make_book(marker))
    assert book.id is not None
    try:
        assert any_books_repo.get_by_id(book.id).copies == []
    finally:
        raw_db.execute('DELETE FROM library.books WHERE id = %(id)s', id=book.id)


def test_not_found(any_books_repo: BooksRepo) -> None:
    with pytest.raises(BookNotFound):
        any_books_repo.get_by_id(-1)


def test_update_nested_collection(
    db_books_repo: DbBooksRepo,
    book_factory: Callable[..., Book],
) -> None:
    book = book_factory(copies=2)
    assert book.id is not None
    book.title = 'Новое название'
    book.copies.pop(0)
    book.add_copy('z-NEW', ShelfLocation(hall='C', rack=5, shelf=5))
    book.copies[0].is_available = False
    db_books_repo.save(book)
    assert db_books_repo.get_by_id(book.id) == book


def test_save_unknown_id(db_books_repo: DbBooksRepo, marker: str) -> None:
    with pytest.raises(BookNotFound):
        db_books_repo.save(make_book(marker, id=-5))


def test_save_invalid_writes_nothing(
    db_books_repo: DbBooksRepo,
    raw_db: RawDb,
    marker: str,
) -> None:
    with pytest.raises(InvalidIsbn):
        db_books_repo.save(make_book(marker, isbn='1'))
    count = raw_db.scalar(
        'SELECT count(*) FROM library.books WHERE title = %(title)s',
        title=f'Книга {marker}',
    )
    assert count == 0


def test_find_by_criteria_matches_domain(
    any_books_repo: BooksRepo,
    marker: str,
    raw_db: RawDb,
) -> None:
    old = any_books_repo.save(make_book(marker, published_year=1990, authors=[marker]))
    new = any_books_repo.save(make_book(marker, published_year=2010, authors=[marker]))
    available = make_book(marker, published_year=2020, authors=[marker, 'Другой'])
    available.add_copy('C', ShelfLocation(hall='A', rack=1, shelf=1))
    any_books_repo.save(available)
    books = [old, new, available]
    cases = {
        'has_available': Book.has_available_copies(),
        'published_after': Book.published_after(year=2000),
        'written_by': Book.written_by(author='Другой'),
        'and': Book.published_after(year=2000) & Book.has_available_copies(),
        'or': Book.published_after(year=2015) | ~Book.published_after(year=1995),
        'not': ~Book.has_available_copies(),
    }
    try:
        ids = {b.id for b in books}
        for criteria in cases.values():
            found = [b for b in any_books_repo.find(criteria) if b.id in ids]
            expected = [b for b in books if criteria.is_satisfied_by(b)]
            assert sorted(b.id for b in found if b.id) == sorted(
                b.id for b in expected if b.id
            )
    finally:
        raw_db.execute(
            'DELETE FROM library.books WHERE id = ANY(%(ids)s)',
            ids=[b.id for b in books],
        )
