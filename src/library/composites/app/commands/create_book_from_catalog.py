import logging
from typing import Any

from classic.db_tools import Engine

from library.app.clock import Clock
from library.app.commands.domain.book import BooksRepo
from library.app.commands.isbn_catalog import IsbnCatalog
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
)
from library.composites.app.logger import logger
from library.composites.infra.clock.system import clock
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo
from library.composites.integrations.isbn_catalog.client import (
    isbn_catalog_client,
)


def create_create_book_from_catalog(
    books: BooksRepo,
    catalog: IsbnCatalog,
    clock_: Clock,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> CreateBookFromCatalog:
    usecase = CreateBookFromCatalog(
        books=books,
        catalog=catalog,
        clock=clock_,
        logger=logger_,
    )
    usecase.run = engine_.transaction(usecase.run)
    return usecase


create_book_from_catalog = create_create_book_from_catalog(
    books=books_repo,
    catalog=isbn_catalog_client,
    clock_=clock,
    engine_=engine,
    logger_=logger,
)
