import logging
from typing import Any

from classic.db_tools import Engine

from library.app.clock import Clock
from library.app.commands.domain.loan import LoansRepo
from library.app.commands.use_cases.loans.extend_loan import ExtendLoan
from library.composites.app.logger import logger
from library.composites.infra.clock.system import clock
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.loans import loans_repo


def create_extend_loan(
    loans: LoansRepo,
    clock_: Clock,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> ExtendLoan:
    usecase = ExtendLoan(loans=loans, clock=clock_, logger=logger_)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


extend_loan = create_extend_loan(
    loans=loans_repo,
    clock_=clock,
    engine_=engine,
    logger_=logger,
)
