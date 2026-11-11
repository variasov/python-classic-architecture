import logging

from library.app.commands.use_cases.readers.register_reader import RegisterReader
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

register_reader = RegisterReader(readers=readers_repo, logger=logger)
register_reader.run = engine.transaction(register_reader.run)  # pyright: ignore[reportAttributeAccessIssue]
