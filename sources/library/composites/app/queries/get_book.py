from classic.db_tools import Engine
from library.app.queries.books.get_book import BookCardGateway, GetBook
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.gateways.book_card_gateway import book_card_gateway


def create_get_book(gateway: BookCardGateway, engine: Engine) -> GetBook:
    query = GetBook(gateway=gateway)
    query.run = engine.transaction(query.run)
    return query


get_book = create_get_book(gateway=book_card_gateway, engine=default_engine)
