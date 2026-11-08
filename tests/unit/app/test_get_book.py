import pytest

from library.app.queries.books.get_book import (
    CopyDTO,
    GetBook,
    GetBookDTO,
    GetBookNotFound,
    GetBookParams,
)


def test_get_book_returns_card(get_book_gateway) -> None:
    dto = GetBookDTO(
        id=1,
        isbn='9780132350884',
        title='Clean Code',
        authors=['Robert Martin'],
        published_year=2008,
        copies=[
            CopyDTO(
                inventory_number='INV-1',
                hall='A',
                rack=1,
                shelf=1,
                is_available=True,
            ),
        ],
    )
    get_book_gateway.result = dto
    usecase = GetBook(gateway=get_book_gateway)
    assert usecase.run(GetBookParams(id=1)) == dto
    assert get_book_gateway.calls == [1]


def test_get_book_not_found(get_book_gateway) -> None:
    usecase = GetBook(gateway=get_book_gateway)
    with pytest.raises(GetBookNotFound) as exc_info:
        usecase.run(GetBookParams(id=999))
    assert exc_info.value.id == 999


def test_get_book_without_copies(get_book_gateway) -> None:
    get_book_gateway.result = GetBookDTO(
        id=1,
        isbn='9780132350884',
        title='Clean Code',
        authors=['Robert Martin'],
        published_year=2008,
        copies=[],
    )
    usecase = GetBook(gateway=get_book_gateway)
    assert usecase.run(GetBookParams(id=1)).copies == []
