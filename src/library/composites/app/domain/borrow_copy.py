from library.app.domain.borrow_copy import BorrowCopy
from library.composites.app.hub import hub
from library.composites.infra.db.repos.copies import copies_repo
from library.composites.infra.db.repos.loans import loans_repo
from library.composites.infra.db.repos.readers import readers_repo

borrow_copy = BorrowCopy(
    readers=readers_repo,
    copies=copies_repo,
    loans=loans_repo,
    hub=hub,
)
