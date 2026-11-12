import logging

import pydantic

from library.app.commands.use_cases.readers.block_reader import BlockReader
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

block_reader = BlockReader(readers=readers_repo, logger=logger)

# fmt: off
block_reader.run = (
    pydantic.validate_call(
    engine.transaction(
    block_reader.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
