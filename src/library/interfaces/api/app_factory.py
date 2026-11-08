from typing import Any, cast

import falcon

from library.interfaces.api.errors import register_error_handlers
from library.interfaces.api.middleware import AuthMiddleware
from library.interfaces.api.resources.book import BookResource
from library.interfaces.api.resources.books import BooksResource
from library.interfaces.api.resources.catalog_books import (
    CatalogBooksResource,
)
from library.interfaces.api.resources.copies import CopiesResource
from library.interfaces.api.resources.loan_extensions import (
    LoanExtensionsResource,
)
from library.interfaces.api.resources.loans import LoansResource
from library.interfaces.api.resources.memberships import (
    MembershipsResource,
)
from library.interfaces.api.resources.reader_blocks import (
    ReaderBlocksResource,
)
from library.interfaces.api.resources.readers import ReadersResource
from library.interfaces.api.resources.returns import ReturnsResource


def create_app(  # noqa: PLR0913
    *,
    books: BooksResource,
    book: BookResource,
    catalog_books: CatalogBooksResource,
    copies: CopiesResource,
    readers: ReadersResource,
    memberships: MembershipsResource,
    reader_blocks: ReaderBlocksResource,
    loans: LoansResource,
    loan_extensions: LoanExtensionsResource,
    returns: ReturnsResource,
    auth: AuthMiddleware | None = None,
) -> falcon.App:
    middleware = [auth or AuthMiddleware(users={})]
    app = falcon.App(middleware=cast('Any', middleware))
    register_error_handlers(app)
    app.add_route('/library/books', books)
    app.add_route('/library/book', book)
    app.add_route('/library/catalog_books', catalog_books)
    app.add_route('/library/copies', copies)
    app.add_route('/library/readers', readers)
    app.add_route('/library/memberships', memberships)
    app.add_route('/library/reader_blocks', reader_blocks)
    app.add_route('/library/loans', loans)
    app.add_route('/library/loan_extensions', loan_extensions)
    app.add_route('/library/returns', returns)
    return app
