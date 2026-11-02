import falcon
import pydantic
from library.app.commands.domain.errors import DomainError
from library.app.errors import AppError
from library.interfaces.api.errors import serialize_app_error, serialize_pydantic_error
from library.interfaces.api.middleware import AccountMiddleware
from library.interfaces.api.resources.books import (
    BookResource,
    BooksResource,
    CatalogBooksResource,
    CopiesResource,
)
from library.interfaces.api.resources.loans import (
    LoanExtensionsResource,
    LoansResource,
    ReturnsResource,
)
from library.interfaces.api.resources.readers import (
    MembershipsResource,
    ReaderBlocksResource,
    ReadersResource,
)

PREFIX = '/library'


def create_app(  # noqa: PLR0913, PLR0917
    users: dict[str, list[str]],
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
) -> falcon.App:
    app = falcon.App(middleware=[AccountMiddleware(users)])
    app.add_error_handler(pydantic.ValidationError, serialize_pydantic_error)
    app.add_error_handler((AppError, DomainError), serialize_app_error)
    app.add_route(f'{PREFIX}/books', books)
    app.add_route(f'{PREFIX}/book', book)
    app.add_route(f'{PREFIX}/catalog_books', catalog_books)
    app.add_route(f'{PREFIX}/copies', copies)
    app.add_route(f'{PREFIX}/readers', readers)
    app.add_route(f'{PREFIX}/memberships', memberships)
    app.add_route(f'{PREFIX}/reader_blocks', reader_blocks)
    app.add_route(f'{PREFIX}/loans', loans)
    app.add_route(f'{PREFIX}/loan_extensions', loan_extensions)
    app.add_route(f'{PREFIX}/returns', returns)
    return app
