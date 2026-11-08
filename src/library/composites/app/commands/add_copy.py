import logging
from typing import Any

from classic.db_tools import Engine

from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.add_copy import AddCopy
from library.composites.app.logger import logger
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo


def create_add_copy(
    books: BooksRepo,
    engine_: Engine[Any],
    logger_: logging.Logger,
) -> AddCopy:
    usecase = AddCopy(books=books, logger=logger_)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


add_copy = create_add_copy(
    books=books_repo,
    engine_=engine,
    logger_=logger,
)
