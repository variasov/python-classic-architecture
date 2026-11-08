from typing import Any

from classic.db_tools import Append, Engine, Entity, Value

from library.app.queries.books.get_book import (
    CopyDTO,
    GetBookDTO,
    GetBookGateway,
)


class GetBookGatewayImpl(GetBookGateway):
    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get(self, id: int) -> GetBookDTO | None:
        book: GetBookDTO | None = (
            self._db.query_from('gateways/books/get_book.sql')
            .map_to(
                GetBookDTO,
                getbookdto=Entity(
                    GetBookDTO,
                    'id',
                    copies=Append(CopyDTO),
                ),
                copydto=Value(CopyDTO),
            )
            .one(id=id)
        )
        return book
