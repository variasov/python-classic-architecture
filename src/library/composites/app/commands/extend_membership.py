import logging

from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
)
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

extend_membership = ExtendMembership(readers=readers_repo, logger=logger)
extend_membership.run = engine.transaction(extend_membership.run)  # pyright: ignore[reportAttributeAccessIssue]
