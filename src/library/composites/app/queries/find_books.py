from typing import Any

from classic.db_tools import Engine

from library.app.queries.books.find_books import (
    FindBooks,
    FindBooksGateway,
)
from library.composites.infra.db.engine import engine
from library.composites.infra.db.gateways.find_books import find_books_gateway


def create_find_books(
    gateway: FindBooksGateway,
    engine_: Engine[Any],
) -> FindBooks:
    usecase = FindBooks(gateway=gateway)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


find_books = create_find_books(
    gateway=find_books_gateway,
    engine_=engine,
)
