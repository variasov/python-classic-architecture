from classic.db_tools import Engine
from library.app.queries.books.find_books import BooksSearchGateway, FindBooks
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.gateways.books_search_gateway import (
    books_search_gateway,
)


def create_find_books(gateway: BooksSearchGateway, engine: Engine) -> FindBooks:
    query = FindBooks(gateway=gateway)
    query.run = engine.transaction(query.run)
    return query


find_books = create_find_books(gateway=books_search_gateway, engine=default_engine)
