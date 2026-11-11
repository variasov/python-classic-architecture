from library.composites.infra.db.engine import engine
from library.infra.db.gateways.find_books import DbFindBooksGateway

find_books_gateway = DbFindBooksGateway(engine)
