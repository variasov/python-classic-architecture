import logging

from classic.db_tools import Engine
from classic.signals import Hub
from library.app.clock import Clock
from library.app.commands.domain.issue_loan import IssueLoan
from library.app.commands.use_cases.loans.issue_loan_command import IssueLoanCommand
from library.composites.app.commands.issue_loan import issue_loan
from library.composites.app.hub import hub as default_hub
from library.composites.app.logger import logger as default_logger
from library.composites.infra.clock.system import clock as default_clock
from library.composites.infra.db.engine import engine as default_engine

# Импорт подписывает уведомитель на сигнал LoanIssued
from library.composites.infra.db.subscribers.loan_issued_notifier import (  # noqa: F401
    loan_issued_notifier,  # pyright: ignore[reportUnusedImport]
)


def create_issue_loan_command(
    issue_loan: IssueLoan,
    clock: Clock,
    hub: Hub,
    engine: Engine,
    logger: logging.Logger,
) -> IssueLoanCommand:
    use_case = IssueLoanCommand(
        issue_loan=issue_loan,
        clock=clock,
        hub=hub,
        logger=logger,
    )
    use_case.run = engine.transaction(use_case.run)
    return use_case


issue_loan_command = create_issue_loan_command(
    issue_loan=issue_loan,
    clock=default_clock,
    hub=default_hub,
    engine=default_engine,
    logger=default_logger,
)
