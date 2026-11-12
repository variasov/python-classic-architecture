import logging

import pydantic

from library.app.commands.readers.extend_membership import (
    ExtendMembership,
)
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

extend_membership = ExtendMembership(readers=readers_repo, logger=logger)

# fmt: off
extend_membership.run = (
    pydantic.validate_call(
    engine.transaction(
    extend_membership.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
