from library.composites.app.commands.create_book_from_catalog import (
    create_book_from_catalog,
)
from library.interfaces.api.resources.catalog_books import (
    CatalogBooksResource,
)

catalog_books_resource = CatalogBooksResource(
    create_book=create_book_from_catalog,
)
