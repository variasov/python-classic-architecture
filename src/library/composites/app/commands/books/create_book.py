import logging

import pydantic

from library.app.commands.books.create_book import CreateBook
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo

logger = logging.getLogger('library')

create_book = CreateBook(books=books_repo, logger=logger)

# fmt: off
create_book.run = (
    pydantic.validate_call(
    engine.transaction(
    create_book.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
