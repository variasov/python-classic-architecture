import logging

from classic.db_tools import Engine
from library.app.commands.domain.reader import ReadersRepo
from library.app.commands.use_cases.readers.extend_membership import ExtendMembership
from library.composites.app.logger import logger as default_logger
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.repos.readers_repo import readers_repo


def create_extend_membership(
    readers: ReadersRepo,
    engine: Engine,
    logger: logging.Logger,
) -> ExtendMembership:
    use_case = ExtendMembership(readers=readers, logger=logger)
    use_case.run = engine.transaction(use_case.run)
    return use_case


extend_membership = create_extend_membership(
    readers=readers_repo,
    engine=default_engine,
    logger=default_logger,
)
