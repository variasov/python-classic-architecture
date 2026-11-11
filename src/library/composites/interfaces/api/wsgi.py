from typing import Any

import falcon

from library.composites.interfaces.api.resources.book import book
from library.composites.interfaces.api.resources.books import books
from library.composites.interfaces.api.resources.catalog_books import catalog_books
from library.composites.interfaces.api.resources.copies import copies
from library.composites.interfaces.api.resources.loan_extensions import (
    loan_extensions,
)
from library.composites.interfaces.api.resources.loans import loans
from library.composites.interfaces.api.resources.memberships import memberships
from library.composites.interfaces.api.resources.reader_blocks import reader_blocks
from library.composites.interfaces.api.resources.readers import readers
from library.composites.interfaces.api.resources.returns import returns
from library.composites.interfaces.api.settings import api_settings
from library.interfaces.api.app import create_app

app: falcon.App[Any, Any] = create_app(
    api_settings,
    books=books,
    copies=copies,
    readers=readers,
    book=book,
    catalog_books=catalog_books,
    memberships=memberships,
    reader_blocks=reader_blocks,
    loans=loans,
    loan_extensions=loan_extensions,
    returns=returns,
)
