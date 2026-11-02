import logging

from classic.db_tools import Engine
from library.app.clock import Clock
from library.app.commands.domain.loan import LoansRepo
from library.app.commands.use_cases.loans.extend_loan import ExtendLoan
from library.composites.app.logger import logger as default_logger
from library.composites.infra.clock.system import clock as default_clock
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.repos.loans_repo import loans_repo


def create_extend_loan(
    loans: LoansRepo,
    clock: Clock,
    engine: Engine,
    logger: logging.Logger,
) -> ExtendLoan:
    use_case = ExtendLoan(loans=loans, clock=clock, logger=logger)
    use_case.run = engine.transaction(use_case.run)
    return use_case


extend_loan = create_extend_loan(
    loans=loans_repo,
    clock=default_clock,
    engine=default_engine,
    logger=default_logger,
)
