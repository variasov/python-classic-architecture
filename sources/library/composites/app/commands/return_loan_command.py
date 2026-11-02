import logging

from classic.db_tools import Engine
from library.app.clock import Clock
from library.app.commands.domain.return_loan import ReturnLoan
from library.app.commands.use_cases.loans.return_loan_command import ReturnLoanCommand
from library.composites.app.commands.return_loan import return_loan
from library.composites.app.logger import logger as default_logger
from library.composites.infra.clock.system import clock as default_clock
from library.composites.infra.db.engine import engine as default_engine


def create_return_loan_command(
    return_loan: ReturnLoan,
    clock: Clock,
    engine: Engine,
    logger: logging.Logger,
) -> ReturnLoanCommand:
    use_case = ReturnLoanCommand(return_loan=return_loan, clock=clock, logger=logger)
    use_case.run = engine.transaction(use_case.run)
    return use_case


return_loan_command = create_return_loan_command(
    return_loan=return_loan,
    clock=default_clock,
    engine=default_engine,
    logger=default_logger,
)
