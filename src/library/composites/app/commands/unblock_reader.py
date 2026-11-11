import logging

from library.app.commands.use_cases.readers.unblock_reader import (
    UnblockReader,
)
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

unblock_reader = UnblockReader(readers=readers_repo, logger=logger)
unblock_reader.run = engine.transaction(unblock_reader.run)  # pyright: ignore[reportAttributeAccessIssue]
