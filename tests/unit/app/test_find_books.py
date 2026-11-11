from collections.abc import Callable
from typing import Any

import pytest

from library.app.queries.books.find_books import (
    BookListItemDTO,
    FindBooks,
    FindBooksParams,
)


def test_returns_books_from_gateway(
    find_books: FindBooks,
    find_books_gateway: Any,
    book_list_item_factory: Callable[..., BookListItemDTO],
) -> None:
    books = [
        book_list_item_factory(id=1, title='Alpha'),
        book_list_item_factory(id=2, title='Beta'),
    ]
    find_books_gateway.books = books

    assert find_books.run(FindBooksParams()) == books


def test_passes_params_to_gateway(
    find_books: FindBooks, find_books_gateway: Any
) -> None:
    params = FindBooksParams(title__contains='война', limit=5, offset=10)

    find_books.run(params)

    assert find_books_gateway.calls == [params]


def test_params_defaults() -> None:
    params = FindBooksParams()

    assert params.title__contains is None
    assert params.author is None
    assert params.only_available is False
    assert params.year_from is None
    assert params.year_to is None
    assert params.order_by == 'title'
    assert params.limit == 20
    assert params.offset == 0


@pytest.mark.parametrize('limit', [1, 50, FindBooksParams.MAX_LIMIT])
def test_params_accept_limit_in_range(limit: int) -> None:
    assert FindBooksParams(limit=limit).limit == limit


@pytest.mark.parametrize('limit', [-1, 0, FindBooksParams.MAX_LIMIT + 1])
def test_params_reject_limit_out_of_range(limit: int) -> None:
    with pytest.raises(ValueError):
        FindBooksParams(limit=limit)


@pytest.mark.parametrize('offset', [0, 1, 1000])
def test_params_accept_non_negative_offset(offset: int) -> None:
    assert FindBooksParams(offset=offset).offset == offset


def test_params_reject_negative_offset() -> None:
    with pytest.raises(ValueError):
        FindBooksParams(offset=-1)


@pytest.mark.parametrize(
    'search',
    [None, 'abc', 'война'],
)
def test_params_accept_search_from_min_length(search: str | None) -> None:
    assert FindBooksParams(title__contains=search).title__contains == search


@pytest.mark.parametrize('search', ['', 'a', 'ab'])
def test_params_reject_short_search(search: str) -> None:
    with pytest.raises(ValueError):
        FindBooksParams(title__contains=search)


@pytest.mark.parametrize(
    ('year_from', 'year_to'),
    [(None, None), (1900, None), (None, 2000), (2000, 2000), (1900, 2000)],
)
def test_params_accept_consistent_years(
    year_from: int | None, year_to: int | None
) -> None:
    params = FindBooksParams(year_from=year_from, year_to=year_to)

    assert params.year_from == year_from
    assert params.year_to == year_to


def test_params_reject_reversed_years() -> None:
    with pytest.raises(ValueError):
        FindBooksParams(year_from=2001, year_to=2000)
