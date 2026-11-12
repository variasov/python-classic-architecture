from library.app.domain.return_copy import ReturnCopy
from library.composites.infra.db.repos.copies import copies_repo
from library.composites.infra.db.repos.loans import loans_repo

return_copy = ReturnCopy(loans=loans_repo, copies=copies_repo)
