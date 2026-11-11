import logging

from library.app.commands.domain.borrow_copy import BorrowCopy
from library.app.commands.use_cases.loans.issue_loan import IssueLoan
from library.composites.app.hub import hub
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.copies import copies_repo
from library.composites.infra.db.repos.loans import loans_repo
from library.composites.infra.db.repos.readers import readers_repo

logger = logging.getLogger('library')

borrow_copy = BorrowCopy(
    readers=readers_repo,
    copies=copies_repo,
    loans=loans_repo,
    hub=hub,
)
issue_loan = IssueLoan(borrow_copy=borrow_copy, logger=logger)
issue_loan.run = engine.transaction(issue_loan.run)  # pyright: ignore[reportAttributeAccessIssue]
