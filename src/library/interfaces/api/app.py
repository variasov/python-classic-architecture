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
from library.interfaces.api.resources.readers import ReadersResource
from library.interfaces.api.settings import ApiSettings


def create_app(
    settings: ApiSettings,
    books: BooksResource,
    copies: CopiesResource,
    readers: ReadersResource,
    book: BookResource,
    catalog_books: CatalogBooksResource,
) -> falcon.App[Any, Any]:
    """Собрать HTTP-приложение: middleware, обработчики ошибок, маршруты"""
    app: falcon.App[Any, Any] = falcon.App(
        middleware=[UserMiddleware(users=settings.USERS)]
    )
    app.add_error_handler(pydantic.ValidationError, serialize_validation_error)
    app.add_error_handler(AuthError, serialize_auth_error)
    app.add_error_handler((AppError, DomainError), serialize_app_error)
    app.add_route('/library/books', books)
    app.add_route('/library/book', book)
    app.add_route('/library/copies', copies)
    app.add_route('/library/readers', readers)
    app.add_route('/library/catalog_books', catalog_books)
    return app
