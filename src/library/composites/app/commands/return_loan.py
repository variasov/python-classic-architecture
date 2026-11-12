import logging

import pydantic

from library.app.commands.domain.return_copy import ReturnCopy
from library.app.commands.use_cases.loans.return_loan import ReturnLoan
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.copies import copies_repo
from library.composites.infra.db.repos.loans import loans_repo

logger = logging.getLogger('library')

return_copy = ReturnCopy(loans=loans_repo, copies=copies_repo)
return_loan = ReturnLoan(return_copy=return_copy, logger=logger)

# fmt: off
return_loan.run = (
    pydantic.validate_call(
    engine.transaction(
    return_loan.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
