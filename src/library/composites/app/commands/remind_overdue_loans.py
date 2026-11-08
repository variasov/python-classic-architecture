import logging
from typing import Any

from classic.db_tools import Engine

from library.app.commands.domain.loan import LoansRepo
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    NotificationsGateway,
    RemindOverdueLoans,
)
from library.composites.app.logger import logger
from library.composites.infra.db.engine import engine
from library.composites.infra.db.gateways.notifications import (
    notifications_gateway,
)
from library.composites.infra.db.repos.loans import loans_repo


def create_remind_overdue_loans(
    loans: LoansRepo,
    notifications: NotificationsGateway,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> RemindOverdueLoans:
    usecase = RemindOverdueLoans(
        loans=loans,
        notifications=notifications,
        logger=logger_,
    )
    usecase.run = engine_.transaction(usecase.run)
    return usecase


remind_overdue_loans = create_remind_overdue_loans(
    loans=loans_repo,
    notifications=notifications_gateway,
    engine_=engine,
    logger_=logger,
)
