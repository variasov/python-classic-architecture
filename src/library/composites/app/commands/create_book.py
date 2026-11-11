import logging

from library.app.commands.use_cases.books.create_book import CreateBook
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo

logger = logging.getLogger('library')

create_book = CreateBook(books=books_repo, logger=logger)
create_book.run = engine.transaction(create_book.run)  # pyright: ignore[reportAttributeAccessIssue]
