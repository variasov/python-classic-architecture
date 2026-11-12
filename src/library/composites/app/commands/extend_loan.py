import logging

import pydantic

from library.app.commands.use_cases.loans.extend_loan import ExtendLoan
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.loans import loans_repo

logger = logging.getLogger('library')

extend_loan = ExtendLoan(loans=loans_repo, logger=logger)

# fmt: off
extend_loan.run = (
    pydantic.validate_call(
    engine.transaction(
    extend_loan.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
