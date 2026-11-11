from library.composites.infra.db.engine import engine
from library.infra.db.gateways.find_loans import DbFindLoansGateway

find_loans_gateway = DbFindLoansGateway(engine)
