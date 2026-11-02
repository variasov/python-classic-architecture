from library.app.commands.domain.issue_loan import IssueLoan
from library.composites.infra.db.repos.books_repo import books_repo
from library.composites.infra.db.repos.loans_repo import loans_repo
from library.composites.infra.db.repos.readers_repo import readers_repo

issue_loan = IssueLoan(readers=readers_repo, books=books_repo, loans=loans_repo)
