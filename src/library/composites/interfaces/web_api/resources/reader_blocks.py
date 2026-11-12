from library.composites.app.commands.readers.block_reader import block_reader
from library.composites.app.commands.readers.unblock_reader import (
    unblock_reader,
)
from library.interfaces.web_api.resources.reader_blocks import ReaderBlocksResource

reader_blocks = ReaderBlocksResource(
    block_reader=block_reader,
    unblock_reader=unblock_reader,
)
