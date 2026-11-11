from library.composites.infra.db.engine import engine
from library.infra.db.gateways.get_book import DbGetBookGateway

get_book_gateway = DbGetBookGateway(engine)
