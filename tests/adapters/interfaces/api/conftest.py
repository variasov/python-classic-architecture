from typing import Any

import pytest
from falcon.testing import TestClient
from library.composites.interfaces.api.factory import create_app
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

USERS = {'admin': ['books.edit'], 'guest': []}


class FakeUseCase:
    """Запоминает полученные параметры, возвращает результат или бросает ошибку."""

    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[Any, ...]] = []

    def run(self, *args: Any) -> Any:
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.result


def fake(use_case: FakeUseCase) -> Any:
    """Фейки не наследуют usecase: структурной совместимости по run достаточно."""
    return use_case


@pytest.fixture
def find_books() -> FakeUseCase:
    return FakeUseCase(result=[])


@pytest.fixture
def create_book() -> FakeUseCase:
    return FakeUseCase(result=1)


@pytest.fixture
def get_book() -> FakeUseCase:
    return FakeUseCase()


@pytest.fixture
def issue_loan() -> FakeUseCase:
    return FakeUseCase(result=5)


@pytest.fixture
def find_loans() -> FakeUseCase:
    return FakeUseCase(result=[])


@pytest.fixture
def register_reader() -> FakeUseCase:
    return FakeUseCase(result=3)


@pytest.fixture
def find_readers() -> FakeUseCase:
    return FakeUseCase(result=[])


@pytest.fixture
def extend_membership() -> FakeUseCase:
    return FakeUseCase()


@pytest.fixture
def extend_loan() -> FakeUseCase:
    return FakeUseCase()


@pytest.fixture
def return_loan() -> FakeUseCase:
    return FakeUseCase()


@pytest.fixture
def block_reader() -> FakeUseCase:
    return FakeUseCase()


@pytest.fixture
def add_copy() -> FakeUseCase:
    return FakeUseCase()


@pytest.fixture
def create_from_catalog() -> FakeUseCase:
    return FakeUseCase(result=9)


@pytest.fixture
def client(
    find_books: FakeUseCase,
    create_book: FakeUseCase,
    get_book: FakeUseCase,
    issue_loan: FakeUseCase,
    find_loans: FakeUseCase,
    register_reader: FakeUseCase,
    find_readers: FakeUseCase,
    extend_membership: FakeUseCase,
    extend_loan: FakeUseCase,
    return_loan: FakeUseCase,
    block_reader: FakeUseCase,
    add_copy: FakeUseCase,
    create_from_catalog: FakeUseCase,
) -> TestClient:
    app = create_app(
        users=USERS,
        books=BooksResource(find_books=fake(find_books), create_book=fake(create_book)),
        book=BookResource(get_book=fake(get_book)),
        catalog_books=CatalogBooksResource(
            create_book_from_catalog=fake(create_from_catalog),
        ),
        copies=CopiesResource(add_copy=fake(add_copy)),
        readers=ReadersResource(
            find_readers=fake(find_readers),
            register_reader=fake(register_reader),
        ),
        memberships=MembershipsResource(extend_membership=fake(extend_membership)),
        reader_blocks=ReaderBlocksResource(block_reader=fake(block_reader)),
        loans=LoansResource(find_loans=fake(find_loans), issue_loan=fake(issue_loan)),
        loan_extensions=LoanExtensionsResource(extend_loan=fake(extend_loan)),
        returns=ReturnsResource(return_loan=fake(return_loan)),
    )
    return TestClient(app)
