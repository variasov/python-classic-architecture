from dataclasses import dataclass
from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
    CreateBookFromCatalogParams,
)
from library.app.roles import Account


@dataclass(frozen=True)
class CatalogBookCreated:
    id: int


class CatalogBooksResource:
    _params_validator: ClassVar[TypeAdapter[CreateBookFromCatalogParams]] = TypeAdapter(
        CreateBookFromCatalogParams,
    )
    _serializer: ClassVar[TypeAdapter[CatalogBookCreated]] = TypeAdapter(
        CatalogBookCreated,
    )

    def __init__(self, create_book: CreateBookFromCatalog) -> None:
        self._create_book = create_book

    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
    ) -> None:
        params = self._params_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        book_id = self._create_book.run(account, params)
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._serializer.dump_json(
            CatalogBookCreated(id=book_id),
        )
