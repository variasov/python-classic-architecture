import logging

from classic.db_tools import Engine
from library.app.commands.domain.book import BooksRepo
from library.app.commands.use_cases.books.add_copy import AddCopy
from library.composites.app.logger import logger as default_logger
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.repos.books_repo import books_repo


def create_add_copy(
    books: BooksRepo,
    engine: Engine,
    logger: logging.Logger,
) -> AddCopy:
    use_case = AddCopy(books=books, logger=logger)
    use_case.run = engine.transaction(use_case.run)
    return use_case


add_copy = create_add_copy(
    books=books_repo,
    engine=default_engine,
    logger=default_logger,
)
