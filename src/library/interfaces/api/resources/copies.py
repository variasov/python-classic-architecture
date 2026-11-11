from dataclasses import dataclass
from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.books.add_copy import AddCopy, AddCopyParams
from library.interfaces.api.middleware import current_account


@dataclass(frozen=True)
class CopyCreated:
    """Контракт ответа на создание экземпляра"""

    id: int


class CopiesResource:
    _create_validator: ClassVar = TypeAdapter(AddCopyParams)
    _created_serializer: ClassVar = TypeAdapter(CopyCreated)

    def __init__(self, add_copy: AddCopy) -> None:
        self._add_copy = add_copy

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        copy_id = self._add_copy.run(params, current_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(CopyCreated(id=copy_id))
