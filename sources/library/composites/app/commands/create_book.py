import logging

from classic.db_tools import Engine
from library.app.clock import Clock
from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.create_book import CreateBook
from library.composites.app.logger import logger as default_logger
from library.composites.infra.clock.system import clock as default_clock
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.repos.books_repo import books_repo


def create_create_book(
    books: BooksRepo,
    clock: Clock,
    engine: Engine,
    logger: logging.Logger,
) -> CreateBook:
    use_case = CreateBook(books=books, clock=clock, logger=logger)
    use_case.run = engine.transaction(use_case.run)
    return use_case


create_book = create_create_book(
    books=books_repo,
    clock=default_clock,
    engine=default_engine,
    logger=default_logger,
)
