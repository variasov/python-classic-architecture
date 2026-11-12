import logging

import pydantic

from library.app.commands.loans.issue_loan import IssueLoan
from library.composites.app.domain.borrow_copy import borrow_copy
from library.composites.infra.db.engine import engine

logger = logging.getLogger('library')

issue_loan = IssueLoan(borrow_copy=borrow_copy, logger=logger)

# fmt: off
issue_loan.run = (
    pydantic.validate_call(
    engine.transaction(
    issue_loan.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
