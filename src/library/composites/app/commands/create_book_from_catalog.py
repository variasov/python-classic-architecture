import logging

from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
)
from library.composites.infra.db.engine import engine
from library.composites.infra.db.repos.books import books_repo
from library.composites.integrations.isbn_catalog.client import isbn_catalog_client

logger = logging.getLogger('library')

create_book_from_catalog = CreateBookFromCatalog(
    books=books_repo, catalog=isbn_catalog_client, logger=logger
)
create_book_from_catalog.run = engine.transaction(  # pyright: ignore[reportAttributeAccessIssue]
    create_book_from_catalog.run
)
