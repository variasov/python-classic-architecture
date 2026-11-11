from typing import Any

from classic.db_tools import Append, Engine, Entity

from library.app.queries.books.get_book import (
    BookCardDTO,
    BookCopyDTO,
    GetBookGateway,
    GetBookParams,
)


class DbGetBookGateway(GetBookGateway):
    """Карточка книги из PostgreSQL"""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def run(self, params: GetBookParams) -> BookCardDTO | None:
        card: BookCardDTO | None = (
            self._db.query_from('gateways/books/get_book.sql')
            .map_to(
                BookCardDTO,
                BookCardDTO=Entity(BookCardDTO, 'id', copies=Append('copy')),
                copy=Entity(BookCopyDTO, 'id'),
            )
            .one(id=params.id)
        )
        return card
