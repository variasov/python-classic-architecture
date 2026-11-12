import falcon

from library.app.commands.readers.block_reader import BlockReader
from library.app.commands.readers.unblock_reader import (
    UnblockReader,
)


class ReaderBlocksResource:
    def __init__(
        self,
        block_reader: BlockReader,
        unblock_reader: UnblockReader,
    ) -> None:
        self._block_reader = block_reader
        self._unblock_reader = unblock_reader

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        self._block_reader.run(req.media, req.context.account)

    def on_delete(self, req: falcon.Request, resp: falcon.Response) -> None:
        self._unblock_reader.run(req.params, req.context.account)  # pyright: ignore[reportArgumentType]
