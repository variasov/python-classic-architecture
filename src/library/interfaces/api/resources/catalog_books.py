from dataclasses import dataclass
from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
    CreateBookFromCatalogParams,
)
from library.interfaces.api.middleware import current_account


@dataclass(frozen=True)
class CatalogBookCreated:
    """Контракт ответа на создание книги из каталога"""

    id: int


class CatalogBooksResource:
    _create_validator: ClassVar = TypeAdapter(CreateBookFromCatalogParams)
    _created_serializer: ClassVar = TypeAdapter(CatalogBookCreated)

    def __init__(self, create_book_from_catalog: CreateBookFromCatalog) -> None:
        self._create_book_from_catalog = create_book_from_catalog

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        book_id = self._create_book_from_catalog.run(
            params, current_account(req)
        )
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(
            CatalogBookCreated(id=book_id)
        )
