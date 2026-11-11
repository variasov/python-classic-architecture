import logging

from library.app.commands.use_cases.books.add_copy import AddCopy
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo
from library.composites.infra.db.repos.copies import copies_repo

logger = logging.getLogger('library')

add_copy = AddCopy(books=books_repo, copies=copies_repo, logger=logger)
add_copy.run = engine.transaction(add_copy.run)  # pyright: ignore[reportAttributeAccessIssue]
