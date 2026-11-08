from library.composites.infra.db.engine import engine
from library.infra.db.gateways.find_books import FindBooksGatewayImpl

find_books_gateway = FindBooksGatewayImpl(db=engine)
