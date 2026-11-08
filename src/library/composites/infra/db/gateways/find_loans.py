from library.composites.infra.db.engine import engine
from library.infra.db.gateways.find_loans import FindLoansGatewayImpl

find_loans_gateway = FindLoansGatewayImpl(db=engine)
