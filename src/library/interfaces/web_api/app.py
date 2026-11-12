from typing import Any

import falcon.media
import orjson
import pydantic

from library.app.domain.errors import DomainError
from library.app.errors import AppError, AuthError
from library.interfaces.web_api.errors import (
    serialize_app_error,
    serialize_auth_error,
    serialize_validation_error,
)
from library.interfaces.web_api.middleware import UserMiddleware
from library.interfaces.web_api.resources.book import BookResource
from library.interfaces.web_api.resources.books import BooksResource
from library.interfaces.web_api.resources.catalog_books import CatalogBooksResource
from library.interfaces.web_api.resources.copies import CopiesResource
from library.interfaces.web_api.resources.loan_extensions import (
    LoanExtensionsResource,
)
from library.interfaces.web_api.resources.loans import LoansResource
from library.interfaces.web_api.resources.memberships import MembershipsResource
from library.interfaces.web_api.resources.reader_blocks import ReaderBlocksResource
from library.interfaces.web_api.resources.readers import ReadersResource
from library.interfaces.web_api.resources.returns import ReturnsResource
from library.interfaces.web_api.settings import ApiSettings


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
    orjson_handler = falcon.media.JSONHandler(
        dumps=orjson.dumps,
        loads=orjson.loads,
    )
    app.req_options.media_handlers[falcon.MEDIA_JSON] = orjson_handler
    app.resp_options.media_handlers[falcon.MEDIA_JSON] = orjson_handler
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
