import logging

from classic.db_tools import Engine
from library.app.commands.domain.reader import ReadersRepo
from library.app.commands.use_cases.readers.block_reader import BlockReader
from library.composites.app.logger import logger as default_logger
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.repos.readers_repo import readers_repo


def create_block_reader(
    readers: ReadersRepo,
    engine: Engine,
    logger: logging.Logger,
) -> BlockReader:
    use_case = BlockReader(readers=readers, logger=logger)
    use_case.run = engine.transaction(use_case.run)
    return use_case


block_reader = create_block_reader(
    readers=readers_repo,
    engine=default_engine,
    logger=default_logger,
)
