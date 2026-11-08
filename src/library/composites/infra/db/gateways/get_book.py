from library.composites.infra.db.engine import engine
from library.infra.db.gateways.get_book import GetBookGatewayImpl

get_book_gateway = GetBookGatewayImpl(db=engine)
