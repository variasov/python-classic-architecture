import logging
from typing import Any

from classic.db_tools import Engine

from library.app.clock import Clock
from library.app.commands.domain.book import BooksRepo
from library.app.commands.domain.loan import LoansRepo
from library.app.commands.domain.return_loan import ReturnLoan
from library.app.commands.use_cases.loans.return_loan import (
    ReturnLoanCommand,
)
from library.composites.app.logger import logger
from library.composites.infra.clock.system import clock
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo
from library.composites.infra.db.repos.loans import loans_repo


def create_return_loan_command(
    books: BooksRepo,
    loans: LoansRepo,
    clock_: Clock,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> ReturnLoanCommand:
    return_loan = ReturnLoan(books=books, loans=loans)
    usecase = ReturnLoanCommand(
        return_loan=return_loan,
        clock=clock_,
        logger=logger_,
    )
    usecase.run = engine_.transaction(usecase.run)
    return usecase


return_loan = create_return_loan_command(
    books=books_repo,
    loans=loans_repo,
    clock_=clock,
    engine_=engine,
    logger_=logger,
)
