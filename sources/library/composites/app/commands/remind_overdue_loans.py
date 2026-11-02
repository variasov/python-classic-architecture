import logging

from classic.db_tools import Engine
from library.app.commands.domain.loan import LoansRepo
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    NotificationsOutbox,
    RemindOverdueLoans,
)
from library.composites.app.logger import logger as default_logger
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.repos.loans_repo import loans_repo
from library.composites.infra.db.repos.notifications_outbox import notifications_outbox


def create_remind_overdue_loans(
    loans: LoansRepo,
    outbox: NotificationsOutbox,
    engine: Engine,
    logger: logging.Logger,
) -> RemindOverdueLoans:
    use_case = RemindOverdueLoans(loans=loans, outbox=outbox, logger=logger)
    use_case.run = engine.transaction(use_case.run)
    return use_case


remind_overdue_loans = create_remind_overdue_loans(
    loans=loans_repo,
    outbox=notifications_outbox,
    engine=default_engine,
    logger=default_logger,
)
