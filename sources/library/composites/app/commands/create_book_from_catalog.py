import logging

from classic.db_tools import Engine
from library.app.clock import Clock
from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
    IsbnCatalog,
)
from library.composites.app.logger import logger as default_logger
from library.composites.infra.clock.system import clock as default_clock
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.repos.books_repo import books_repo
from library.composites.integrations.isbn_catalog.client import isbn_catalog_client


def create_create_book_from_catalog(
    books: BooksRepo,
    catalog: IsbnCatalog,
    clock: Clock,
    engine: Engine,
    logger: logging.Logger,
) -> CreateBookFromCatalog:
    use_case = CreateBookFromCatalog(
        books=books,
        catalog=catalog,
        clock=clock,
        logger=logger,
    )
    use_case.run = engine.transaction(use_case.run)
    return use_case


create_book_from_catalog = create_create_book_from_catalog(
    books=books_repo,
    catalog=isbn_catalog_client,
    clock=default_clock,
    engine=default_engine,
    logger=default_logger,
)
