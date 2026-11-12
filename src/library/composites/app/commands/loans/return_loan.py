import logging

import pydantic

from library.app.commands.loans.return_loan import ReturnLoan
from library.composites.app.domain.return_copy import return_copy
from library.composites.infra.db.engine import engine

logger = logging.getLogger('library')

return_loan = ReturnLoan(return_copy=return_copy, logger=logger)

# fmt: off
return_loan.run = (
    pydantic.validate_call(
    engine.transaction(
    return_loan.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
