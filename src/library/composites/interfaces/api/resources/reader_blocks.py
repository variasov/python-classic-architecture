from library.composites.app.commands.block_reader import block_reader
from library.interfaces.api.resources.reader_blocks import (
    ReaderBlocksResource,
)

reader_blocks_resource = ReaderBlocksResource(block_reader=block_reader)
