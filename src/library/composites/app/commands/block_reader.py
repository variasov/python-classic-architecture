import logging

from library.app.commands.use_cases.readers.block_reader import BlockReader
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

block_reader = BlockReader(readers=readers_repo, logger=logger)
block_reader.run = engine.transaction(block_reader.run)  # pyright: ignore[reportAttributeAccessIssue]
