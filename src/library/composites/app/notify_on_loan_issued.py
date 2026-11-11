import logging

from library.app.commands.domain.notify_on_loan_issued import NotifyOnLoanIssued
from library.composites.app.hub import hub
from library.composites.infra.db.repos.notifications import notifications_repo

logger = logging.getLogger('library')

notify_on_loan_issued = NotifyOnLoanIssued(
    hub=hub,
    notifications=notifications_repo,
    logger=logger,
)
