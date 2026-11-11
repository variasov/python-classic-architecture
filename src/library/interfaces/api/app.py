from typing import Any

import falcon
import pydantic

from library.app.commands.domain.errors import DomainError
from library.app.errors import AppError, AuthError
from library.interfaces.api.errors import (
    serialize_app_error,
    serialize_auth_error,
    serialize_validation_error,
)
from library.interfaces.api.middleware import UserMiddleware
from library.interfaces.api.resources.book import BookResource
from library.interfaces.api.resources.books import BooksResource
from library.interfaces.api.resources.catalog_books import CatalogBooksResource
from library.interfaces.api.resources.copies import CopiesResource
from library.interfaces.api.resources.loan_extensions import (
    LoanExtensionsResource,
)
from library.interfaces.api.resources.loans import LoansResource
from library.interfaces.api.resources.memberships import MembershipsResource
from library.interfaces.api.resources.reader_blocks import ReaderBlocksResource
from library.interfaces.api.resources.readers import ReadersResource
from library.interfaces.api.resources.returns import ReturnsResource
from library.interfaces.api.settings import ApiSettings


def create_app(
    settings: ApiSettings,
    books: BooksResource,
    copies: CopiesResource,
    readers: ReadersResource,
    book: BookResource,
    catalog_books: CatalogBooksResource,
    memberships: MembershipsResource,
    reader_blocks: ReaderBlocksResource,
    loans: LoansResource,
    loan_extensions: LoanExtensionsResource,
    returns: ReturnsResource,
) -> falcon.App[Any, Any]:
    """Собрать HTTP-приложение: middleware, обработчики ошибок, маршруты."""
    app: falcon.App[Any, Any] = falcon.App(
        middleware=[UserMiddleware(users=settings.USERS)],
    )
    app.add_error_handler(pydantic.ValidationError, serialize_validation_error)
    app.add_error_handler(AuthError, serialize_auth_error)
    app.add_error_handler((AppError, DomainError), serialize_app_error)
    app.add_route('/library/books', books)
    app.add_route('/library/book', book)
    app.add_route('/library/copies', copies)
    app.add_route('/library/readers', readers)
    app.add_route('/library/catalog_books', catalog_books)
    app.add_route('/library/memberships', memberships)
    app.add_route('/library/reader_blocks', reader_blocks)
    app.add_route('/library/loans', loans)
    app.add_route('/library/loan_extensions', loan_extensions)
    app.add_route('/library/returns', returns)
    return app
