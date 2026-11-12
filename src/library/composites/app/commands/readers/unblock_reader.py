import logging

import pydantic

from library.app.commands.readers.unblock_reader import (
    UnblockReader,
)
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

unblock_reader = UnblockReader(readers=readers_repo, logger=logger)

# fmt: off
unblock_reader.run = (
    pydantic.validate_call(
    engine.transaction(
    unblock_reader.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
