from library.composites.infra.db.engine import engine
from library.infra.db.gateways.books_search_gateway import DbBooksSearchGateway

books_search_gateway = DbBooksSearchGateway(engine=engine)
