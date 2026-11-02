from library.app.commands.domain.return_loan import ReturnLoan
from library.composites.infra.db.repos.books_repo import books_repo
from library.composites.infra.db.repos.loans_repo import loans_repo

return_loan = ReturnLoan(loans=loans_repo, books=books_repo)
