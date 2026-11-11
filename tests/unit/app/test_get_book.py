from collections.abc import Callable
from typing import Any

import pytest

from library.app.queries.books.get_book import (
    BookCardDTO,
    BookCopyDTO,
    GetBook,
    GetBookNotFound,
    GetBookParams,
)


def test_returns_card_from_gateway(
    get_book: GetBook,
    get_book_gateway: Any,
    book_card_factory: Callable[..., BookCardDTO],
    book_copy_factory: Callable[..., BookCopyDTO],
) -> None:
    card = book_card_factory(
        copies=[
            book_copy_factory(id=10, inventory_number='INV-10'),
            book_copy_factory(id=11, inventory_number='INV-11'),
        ],
    )
    get_book_gateway.card = card

    assert get_book.run(GetBookParams(id=1)) == card


def test_passes_params_to_gateway(
    get_book: GetBook,
    get_book_gateway: Any,
    book_card_factory: Callable[..., BookCardDTO],
) -> None:
    get_book_gateway.card = book_card_factory()

    get_book.run(GetBookParams(id=42))

    assert get_book_gateway.calls == [GetBookParams(id=42)]


def test_missing_book_raises(
    get_book: GetBook,
    get_book_gateway: Any,
) -> None:
    get_book_gateway.card = None

    with pytest.raises(GetBookNotFound) as error:
        get_book.run(GetBookParams(id=404))

    assert error.value.id == 404
