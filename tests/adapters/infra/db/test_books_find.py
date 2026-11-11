from collections.abc import Callable

import pytest
from classic.criteria import Criteria, ReturnsTrue

from library.app.commands.domain.book import Book, BooksRepo
from library.infra.db.repos.books import DbBooksRepo


@pytest.fixture
def seeded_books(
    db_books_repo: DbBooksRepo,
    book_factory: Callable[..., Book],
) -> list[Book]:
    return [
        db_books_repo.save(
            book_factory(title='Ранняя', published_year=1900, authors=['Первый']),
        ),
        db_books_repo.save(
            book_factory(title='Средняя', published_year=1950, authors=['Второй']),
        ),
        db_books_repo.save(
            book_factory(title='Поздняя', published_year=2000, authors=['Первый']),
        ),
    ]


@pytest.mark.parametrize(
    'criteria',
    [
        Book.published_after(year=1940),
        Book.written_by(author='Первый'),
        Book.published_after(year=1940) & Book.written_by(author='Первый'),
        Book.published_after(year=1940) | Book.written_by(author='Второй'),
        ~Book.written_by(author='Второй'),
    ],
)
def test_criteria_sql_matches_domain(
    db_books_repo: DbBooksRepo,
    seeded_books: list[Book],
    criteria: Criteria[Book],
) -> None:
    found = db_books_repo.find(criteria)
    expected = [book for book in seeded_books if criteria.is_satisfied_by(book)]

    assert [book.id for book in found] == [book.id for book in expected]


def test_find_returns_all_without_filters(
    db_books_repo: BooksRepo,
    seeded_books: list[Book],
) -> None:
    assert len(db_books_repo.find(ReturnsTrue())) == 3
