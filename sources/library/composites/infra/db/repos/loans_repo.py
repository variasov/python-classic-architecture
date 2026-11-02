from library.composites.infra.db.engine import engine
from library.infra.db.repos.loans_repo import DbLoansRepo

loans_repo = DbLoansRepo(engine=engine)
