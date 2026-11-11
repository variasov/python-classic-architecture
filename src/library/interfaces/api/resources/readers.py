from dataclasses import dataclass
from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.readers.register_reader import (
    RegisterReader,
    RegisterReaderParams,
)
from library.app.queries.readers.find_readers import (
    FindReaders,
    FindReadersParams,
    ReaderListItemDTO,
)
from library.interfaces.api.middleware import current_account


@dataclass(frozen=True)
class ReaderCreated:
    """Контракт ответа на регистрацию читателя."""

    id: int


class ReadersResource:
    _query_validator: ClassVar = TypeAdapter(FindReadersParams)
    _readers_serializer: ClassVar = TypeAdapter(list[ReaderListItemDTO])
    _create_validator: ClassVar = TypeAdapter(RegisterReaderParams)
    _created_serializer: ClassVar = TypeAdapter(ReaderCreated)

    def __init__(
        self,
        find_readers: FindReaders,
        register_reader: RegisterReader,
    ) -> None:
        self._find_readers = find_readers
        self._register_reader = register_reader

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._query_validator.validate_python(req.params)
        readers = self._find_readers.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._readers_serializer.dump_json(readers)

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        reader_id = self._register_reader.run(params, current_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(ReaderCreated(id=reader_id))
