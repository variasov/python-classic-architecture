from library.composites.infra.db.engine import engine
from library.infra.db.repos.loans import LoansRepository

loans_repo = LoansRepository(db=engine)
