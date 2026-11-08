import logging
from typing import Any

from classic.db_tools import Engine
from classic.signals import Hub

from library.app.clock import Clock
from library.app.commands.domain.book import BooksRepo
from library.app.commands.domain.issue_loan import IssueLoan
from library.app.commands.domain.loan import LoansRepo
from library.app.commands.domain.reader import ReadersRepo
from library.app.commands.use_cases.loans.issue_loan import IssueLoanCommand
from library.composites.app.hub import hub
from library.composites.app.logger import logger
from library.composites.infra.clock.system import clock
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo
from library.composites.infra.db.repos.loans import loans_repo
from library.composites.infra.db.repos.readers import readers_repo


def create_issue_loan_command(  # noqa: PLR0913, PLR0917
    readers: ReadersRepo,
    books: BooksRepo,
    loans: LoansRepo,
    clock_: Clock,
    hub_: Hub,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> IssueLoanCommand:
    issue_loan = IssueLoan(
        readers=readers,
        books=books,
        loans=loans,
    )
    usecase = IssueLoanCommand(
        issue_loan=issue_loan,
        clock=clock_,
        hub=hub_,
        logger=logger_,
    )
    usecase.run = engine_.transaction(usecase.run)
    return usecase


issue_loan = create_issue_loan_command(
    readers=readers_repo,
    books=books_repo,
    loans=loans_repo,
    clock_=clock,
    hub_=hub,
    engine_=engine,
    logger_=logger,
)
