import logging
from typing import Any

from classic.db_tools import Engine

from library.app.clock import Clock
from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.create_book import CreateBook
from library.composites.app.logger import logger
from library.composites.infra.clock.system import clock
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo


def create_create_book(
    books: BooksRepo,
    clock_: Clock,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> CreateBook:
    usecase = CreateBook(books=books, clock=clock_, logger=logger_)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


create_book = create_create_book(
    books=books_repo,
    clock_=clock,
    engine_=engine,
    logger_=logger,
)
