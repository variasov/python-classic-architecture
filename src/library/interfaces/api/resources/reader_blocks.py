from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.readers.block_reader import (
    BlockReader,
    BlockReaderParams,
)
from library.app.commands.use_cases.readers.unblock_reader import (
    UnblockReader,
    UnblockReaderParams,
)
from library.interfaces.api.middleware import current_account


class ReaderBlocksResource:
    _block_validator: ClassVar = TypeAdapter(BlockReaderParams)
    _unblock_validator: ClassVar = TypeAdapter(UnblockReaderParams)

    def __init__(
        self, block_reader: BlockReader, unblock_reader: UnblockReader
    ) -> None:
        self._block_reader = block_reader
        self._unblock_reader = unblock_reader

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._block_validator.validate_json(req.bounded_stream.read())
        self._block_reader.run(params, current_account(req))

    def on_delete(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._unblock_validator.validate_python(req.params)
        self._unblock_reader.run(params, current_account(req))
