import logging
from typing import Any

from classic.db_tools import Engine

from library.app.commands.domain.reader import ReadersRepo
from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
)
from library.composites.app.logger import logger
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.readers import readers_repo


def create_extend_membership(
    readers: ReadersRepo,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> ExtendMembership:
    usecase = ExtendMembership(readers=readers, logger=logger_)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


extend_membership = create_extend_membership(
    readers=readers_repo,
    engine_=engine,
    logger_=logger,
)
