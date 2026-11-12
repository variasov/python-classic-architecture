import logging

import pydantic

from library.app.commands.readers.register_reader import RegisterReader
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

register_reader = RegisterReader(readers=readers_repo, logger=logger)

# fmt: off
register_reader.run = (
    pydantic.validate_call(
    engine.transaction(
    register_reader.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
