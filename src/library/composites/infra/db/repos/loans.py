from library.composites.infra.db.engine import engine
from library.infra.db.repos.loans import DbLoansRepo

loans_repo = DbLoansRepo(engine)
