import pytest

from library.app.queries.books.find_books import (
    BookDTO,
    FindBooks,
    FindBooksParams,
)


def test_find_books_delegates_to_gateway(find_books_gateway) -> None:
    dto = BookDTO(
        id=1,
        isbn='9780132350884',
        title='Clean Code',
        authors=['Robert Martin'],
        published_year=2008,
    )
    find_books_gateway.result = [dto]
    usecase = FindBooks(gateway=find_books_gateway)
    params = FindBooksParams(title__contains='Clean')
    assert usecase.run(params) == [dto]
    assert find_books_gateway.calls == [params]


def test_find_books_short_search_returns_empty(
    find_books_gateway,
) -> None:
    usecase = FindBooks(gateway=find_books_gateway)
    result = usecase.run(FindBooksParams(title__contains='ab'))
    assert result == []
    assert find_books_gateway.calls == []


def test_find_books_empty_search_delegates(find_books_gateway) -> None:
    usecase = FindBooks(gateway=find_books_gateway)
    usecase.run(FindBooksParams())
    assert find_books_gateway.calls == [FindBooksParams()]


@pytest.mark.parametrize('limit', [0, -1, 101])
def test_find_books_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError) as exc_info:
        FindBooksParams(limit=limit)
    assert str(exc_info.value) == 'limit должен быть от 1 до 100'


@pytest.mark.parametrize('limit', [1, 100])
def test_find_books_limit_boundaries(limit: int) -> None:
    assert FindBooksParams(limit=limit).limit == limit


def test_find_books_negative_offset() -> None:
    with pytest.raises(ValueError) as exc_info:
        FindBooksParams(offset=-1)
    assert str(exc_info.value) == 'offset не может быть отрицательным'


def test_find_books_year_range_consistency() -> None:
    with pytest.raises(ValueError) as exc_info:
        FindBooksParams(year_from=2020, year_to=2010)
    assert str(exc_info.value) == 'year_from не может быть больше year_to'


def test_find_books_year_range_boundary() -> None:
    params = FindBooksParams(year_from=2010, year_to=2010)
    assert params.year_from == 2010
    assert params.year_to == 2010


def test_find_books_short_search_boundary() -> None:
    params = FindBooksParams(title__contains='abc')
    assert params.MIN_SEARCH_LENGTH == 3


def test_find_books_search_with_min_length_delegates(
    find_books_gateway,
) -> None:
    usecase = FindBooks(gateway=find_books_gateway)
    params = FindBooksParams(title__contains='abc')
    usecase.run(params)
    assert find_books_gateway.calls == [params]
