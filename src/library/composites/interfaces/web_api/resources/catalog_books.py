from library.composites.app.commands.books.create_book_from_catalog import (
    create_book_from_catalog,
)
from library.interfaces.web_api.resources.catalog_books import CatalogBooksResource

catalog_books = CatalogBooksResource(
    create_book_from_catalog=create_book_from_catalog,
)
