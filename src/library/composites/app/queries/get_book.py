from typing import Any

from classic.db_tools import Engine

from library.app.queries.books.get_book import GetBook, GetBookGateway
from library.composites.infra.db.engine import engine
from library.composites.infra.db.gateways.get_book import get_book_gateway


def create_get_book(
    gateway: GetBookGateway,
    engine_: Engine[Any],
) -> GetBook:
    usecase = GetBook(gateway=gateway)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


get_book = create_get_book(
    gateway=get_book_gateway,
    engine_=engine,
)
