from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.readers.block_reader import (
    BlockReader,
    BlockReaderParams,
)
from library.app.roles import Account


class ReaderBlocksResource:
    _params_validator: ClassVar[TypeAdapter[BlockReaderParams]] = TypeAdapter(
        BlockReaderParams,
    )

    def __init__(self, block_reader: BlockReader) -> None:
        self._block_reader = block_reader

    def on_post(
        self,
        req: falcon.Request,
        _resp: falcon.Response,
    ) -> None:
        params = self._params_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        self._block_reader.run(account, params)
