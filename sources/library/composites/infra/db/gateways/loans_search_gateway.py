from library.composites.infra.db.engine import engine
from library.infra.db.gateways.loans_search_gateway import DbLoansSearchGateway

loans_search_gateway = DbLoansSearchGateway(engine=engine)
