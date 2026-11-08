from library.composites.infra.db.subscribers.loan_issued import (
    loan_issued_subscriber as _loan_issued_subscriber,  # noqa: F401  # pyright: ignore[reportUnusedImport]
)
from library.composites.interfaces.api.resources.book import book_resource
from library.composites.interfaces.api.resources.books import (
    books_resource,
)
from library.composites.interfaces.api.resources.catalog_books import (
    catalog_books_resource,
)
from library.composites.interfaces.api.resources.copies import (
    copies_resource,
)
from library.composites.interfaces.api.resources.loan_extensions import (
    loan_extensions_resource,
)
from library.composites.interfaces.api.resources.loans import (
    loans_resource,
)
from library.composites.interfaces.api.resources.memberships import (
    memberships_resource,
)
from library.composites.interfaces.api.resources.reader_blocks import (
    reader_blocks_resource,
)
from library.composites.interfaces.api.resources.readers import (
    readers_resource,
)
from library.composites.interfaces.api.resources.returns import (
    returns_resource,
)
from library.composites.interfaces.api.settings import settings
from library.interfaces.api.app_factory import create_app
from library.interfaces.api.middleware import AuthMiddleware


def create_auth() -> AuthMiddleware:
    return AuthMiddleware(
        users={
            user.login: frozenset(user.permissions)
            for user in settings.USERS
        },
    )


app = create_app(
    books=books_resource,
    book=book_resource,
    catalog_books=catalog_books_resource,
    copies=copies_resource,
    readers=readers_resource,
    memberships=memberships_resource,
    reader_blocks=reader_blocks_resource,
    loans=loans_resource,
    loan_extensions=loan_extensions_resource,
    returns=returns_resource,
    auth=create_auth(),
)
