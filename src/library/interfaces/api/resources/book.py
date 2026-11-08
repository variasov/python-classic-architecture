from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.queries.books.get_book import (
    GetBook,
    GetBookDTO,
    GetBookParams,
)


class BookResource:
    _params_validator: ClassVar[TypeAdapter[GetBookParams]] = TypeAdapter(
        GetBookParams,
    )
    _serializer: ClassVar[TypeAdapter[GetBookDTO]] = TypeAdapter(GetBookDTO)

    def __init__(self, get_book: GetBook) -> None:
        self._get_book = get_book

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
    ) -> None:
        params = self._params_validator.validate_python(req.params)
        book = self._get_book.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._serializer.dump_json(book)
