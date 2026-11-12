import logging

from library.app.commands.loans.remind_overdue_loans import (
    RemindOverdueLoans,
)
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.loans import loans_repo
from library.composites.infra.db.repos.notifications import notifications_repo

logger = logging.getLogger('library')

remind_overdue_loans = RemindOverdueLoans(
    loans=loans_repo,
    notifications=notifications_repo,
    logger=logger,
)
remind_overdue_loans.run = engine.transaction(remind_overdue_loans.run)  # pyright: ignore[reportAttributeAccessIssue]
