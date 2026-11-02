from typing import Any, cast

from classic.db_tools import Append, Engine, Entity
from library.app.queries.books.get_book import (
    BookCard,
    BookCardGateway,
    CopyCard,
    ShelfCard,
)


def _make_copy_card(
    *,
    inventory_number: str,
    is_available: bool,
    hall: str,
    rack: int,
    shelf: int,
) -> CopyCard:
    return CopyCard(
        inventory_number=inventory_number,
        is_available=is_available,
        shelf=ShelfCard(hall=hall, rack=rack, shelf=shelf),
    )


class DbBookCardGateway(BookCardGateway):
    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def get(self, id: int) -> BookCard | None:
        return cast(
            'BookCard | None',
            self._db.query_from('gateways/books/get_card.sql')
            .map_to(
                BookCard,
                BookCard=Entity(BookCard, 'id', copies=Append('copycard')),
                CopyCard=Entity(cast('Any', _make_copy_card), 'inventory_number'),
            )
            .one(id=id),
        )
