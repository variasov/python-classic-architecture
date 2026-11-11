from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.queries.books.get_book import (
    BookCardDTO,
    GetBook,
    GetBookParams,
)


class BookResource:
    _query_validator: ClassVar = TypeAdapter(GetBookParams)
    _card_serializer: ClassVar = TypeAdapter(BookCardDTO)

    def __init__(self, get_book: GetBook) -> None:
        self._get_book = get_book

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._query_validator.validate_python(req.params)
        card = self._get_book.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._card_serializer.dump_json(card)
