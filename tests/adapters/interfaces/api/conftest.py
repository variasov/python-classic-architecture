from dataclasses import dataclass, field
from typing import Any, cast

import pytest
from falcon import testing

from library.interfaces.api.app_factory import create_app
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
from library.interfaces.api.resources.memberships import MembershipsResource
from library.interfaces.api.resources.reader_blocks import (
    ReaderBlocksResource,
)
from library.interfaces.api.resources.readers import ReadersResource
from library.interfaces.api.resources.returns import ReturnsResource


class FakeUseCase:
    def __init__(
        self,
        result: Any = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[Any, ...]] = []

    def run(self, *args: Any, **kwargs: Any) -> Any:
        self.calls.append((*args, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


@dataclass
class ApiHarness:
    find_books: FakeUseCase = field(default_factory=FakeUseCase)
    create_book: FakeUseCase = field(default_factory=FakeUseCase)
    get_book: FakeUseCase = field(default_factory=FakeUseCase)
    create_book_from_catalog: FakeUseCase = field(
        default_factory=FakeUseCase,
    )
    add_copy: FakeUseCase = field(default_factory=FakeUseCase)
    find_readers: FakeUseCase = field(default_factory=FakeUseCase)
    register_reader: FakeUseCase = field(default_factory=FakeUseCase)
    extend_membership: FakeUseCase = field(default_factory=FakeUseCase)
    block_reader: FakeUseCase = field(default_factory=FakeUseCase)
    find_loans: FakeUseCase = field(default_factory=FakeUseCase)
    issue_loan: FakeUseCase = field(default_factory=FakeUseCase)
    extend_loan: FakeUseCase = field(default_factory=FakeUseCase)
    return_loan: FakeUseCase = field(default_factory=FakeUseCase)
    client: testing.TestClient = field(init=False)

    def __post_init__(self) -> None:
        app = create_app(
            books=BooksResource(
                find_books=cast('Any', self.find_books),
                create_book=cast('Any', self.create_book),
            ),
            book=BookResource(get_book=cast('Any', self.get_book)),
            catalog_books=CatalogBooksResource(
                create_book=cast('Any', self.create_book_from_catalog),
            ),
            copies=CopiesResource(add_copy=cast('Any', self.add_copy)),
            readers=ReadersResource(
                find_readers=cast('Any', self.find_readers),
                register_reader=cast('Any', self.register_reader),
            ),
            memberships=MembershipsResource(
                extend_membership=cast('Any', self.extend_membership),
            ),
            reader_blocks=ReaderBlocksResource(
                block_reader=cast('Any', self.block_reader),
            ),
            loans=LoansResource(
                find_loans=cast('Any', self.find_loans),
                issue_loan=cast('Any', self.issue_loan),
            ),
            loan_extensions=LoanExtensionsResource(
                extend_loan=cast('Any', self.extend_loan),
            ),
            returns=ReturnsResource(
                return_loan=cast('Any', self.return_loan),
            ),
            auth=AuthMiddleware(
                users={
                    'admin': frozenset(
                        {
                            'books.edit',
                            'readers.edit',
                            'loans.edit',
                        },
                    ),
                },
            ),
        )
        self.client = testing.TestClient(app)


@pytest.fixture
def api() -> ApiHarness:
    return ApiHarness()
