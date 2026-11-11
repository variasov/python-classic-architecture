from typing import Any

import falcon

from library.composites.interfaces.api.resources.book import book
from library.composites.interfaces.api.resources.books import books
from library.composites.interfaces.api.resources.catalog_books import catalog_books
from library.composites.interfaces.api.resources.copies import copies
from library.composites.interfaces.api.settings import api_settings
from library.interfaces.api.app import create_app

app: falcon.App[Any, Any] = create_app(
    api_settings,
    books=books,
    copies=copies,
    book=book,
    catalog_books=catalog_books,
)
