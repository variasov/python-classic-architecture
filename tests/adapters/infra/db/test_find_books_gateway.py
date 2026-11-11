from collections.abc import Callable

import pytest

from library.app.commands.domain.book import Book, BooksRepo
from library.app.commands.domain.copy import CopiesRepo, Copy
from library.app.queries.books.find_books import (
    BookListItemDTO,
    FindBooksGateway,
    FindBooksParams,
)


@pytest.fixture
def seeded_books(
    db_books_repo: BooksRepo,
    db_copies_repo: CopiesRepo,
    book_factory: Callable[..., Book],
    copy_factory: Callable[..., Copy],
) -> dict[str, Book]:
    books = {
        'Alpha': db_books_repo.save(
            book_factory(
                title='Alpha',
                authors=['Ann'],
                published_year=1900,
            ),
        ),
        'Beta': db_books_repo.save(
            book_factory(
                title='Beta',
                authors=['Bob'],
                published_year=1950,
            ),
        ),
        'Gamma': db_books_repo.save(
            book_factory(
                title='Gamma',
                authors=['Ann', 'Bob'],
                published_year=2000,
            ),
        ),
        'Delta': db_books_repo.save(
            book_factory(
                title='Delta',
                authors=['Dan'],
                published_year=2010,
            ),
        ),
    }
    assert books['Alpha'].id is not None
    assert books['Beta'].id is not None
    assert books['Delta'].id is not None
    available = db_copies_repo.save(
        copy_factory(
            book_id=books['Alpha'].id,
            inventory_number='INV-FIND-1',
        ),
    )
    taken = db_copies_repo.save(
        copy_factory(
            book_id=books['Alpha'].id,
            inventory_number='INV-FIND-2',
        ),
    )
    taken.take()
    db_copies_repo.save(taken)
    assert available.id is not None
    beta_copy = db_copies_repo.save(
        copy_factory(
            book_id=books['Beta'].id,
            inventory_number='INV-FIND-3',
        ),
    )
    beta_copy.take()
    db_copies_repo.save(beta_copy)
    db_copies_repo.save(
        copy_factory(
            book_id=books['Delta'].id,
            inventory_number='INV-FIND-4',
        ),
    )
    return books


def _titles(books: list[BookListItemDTO]) -> list[str]:
    return [book.title for book in books]


def test_without_filters_returns_all_ordered_by_title(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(FindBooksParams())

    assert _titles(found) == ['Alpha', 'Beta', 'Delta', 'Gamma']


def test_filters_by_title_substring_case_insensitively(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(
        FindBooksParams(title__contains='AMM'),
    )

    assert _titles(found) == ['Gamma']


def test_filters_by_author(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(FindBooksParams(author='Ann'))

    assert _titles(found) == ['Alpha', 'Gamma']


def test_filters_by_availability(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(FindBooksParams(only_available=True))

    assert _titles(found) == ['Alpha', 'Delta']


def test_filters_by_year_from(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(FindBooksParams(year_from=1950))

    assert _titles(found) == ['Beta', 'Delta', 'Gamma']


def test_filters_by_year_to(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(FindBooksParams(year_to=1950))

    assert _titles(found) == ['Alpha', 'Beta']


def test_combines_all_filters(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(
        FindBooksParams(
            title__contains='lph',
            author='Ann',
            only_available=True,
            year_from=1900,
            year_to=1950,
        ),
    )

    assert _titles(found) == ['Alpha']


def test_combines_author_and_years_without_availability(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(
        FindBooksParams(
            title__contains='eta',
            author='Bob',
            only_available=False,
            year_from=1900,
            year_to=2000,
        ),
    )

    assert _titles(found) == ['Beta']


def test_orders_by_published_year(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(
        FindBooksParams(order_by='published_year'),
    )

    assert _titles(found) == ['Alpha', 'Beta', 'Gamma', 'Delta']


@pytest.mark.parametrize(
    ('limit', 'offset', 'expected'),
    [
        (2, 0, ['Alpha', 'Beta']),
        (2, 2, ['Delta', 'Gamma']),
        (1, 3, ['Gamma']),
        (10, 10, []),
    ],
)
def test_paginates(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
    limit: int,
    offset: int,
    expected: list[str],
) -> None:
    found = db_find_books_gateway.run(
        FindBooksParams(limit=limit, offset=offset),
    )

    assert _titles(found) == expected


def test_empty_result(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(
        FindBooksParams(title__contains='zzz'),
    )

    assert found == []


def test_maps_dto_fields(
    db_find_books_gateway: FindBooksGateway,
    seeded_books: dict[str, Book],
) -> None:
    found = db_find_books_gateway.run(FindBooksParams())

    by_title = {book.title: book for book in found}
    assert by_title['Gamma'].authors == ['Ann', 'Bob']
    assert by_title['Gamma'].available_copies == 0
    assert by_title['Alpha'].available_copies == 1
    assert by_title['Alpha'].published_year == 1900
    assert by_title['Alpha'].id == seeded_books['Alpha'].id
