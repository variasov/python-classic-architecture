import logging

import pydantic

from library.app.commands.use_cases.books.add_copy import AddCopy
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo
from library.composites.infra.db.repos.copies import copies_repo

logger = logging.getLogger('library')

add_copy = AddCopy(books=books_repo, copies=copies_repo, logger=logger)

# fmt: off
add_copy.run = (
    pydantic.validate_call(
    engine.transaction(
    add_copy.run
)))  # pyright: ignore[reportAttributeAccessIssue]
# fmt: on
