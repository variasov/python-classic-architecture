import json
from dataclasses import dataclass
from typing import Any

import falcon
import pytest
from falcon import testing
from pydantic import TypeAdapter

from library.app.commands.domain.errors import DomainError
from library.app.errors import AppError
from library.app.queries.books.find_books import BookListItemDTO
from library.app.queries.books.get_book import BookCardDTO, BookCopyDTO
from library.app.roles import PermissionDenied
from library.interfaces.api.app import create_app
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


@dataclass
class ProbeAppError(AppError):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class ProbeDomainError(DomainError):
    message: str

    def __str__(self) -> str:
        return self.message


class ProbeResource:
    """Тестовый ресурс: отдаёт Account и умеет бросать ошибки всех видов"""

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        account = getattr(req.context, 'account', None)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = json.dumps(
            {
                'login': account.login if account else None,
                'permissions': list(account.permissions) if account else [],
            }
        ).encode()

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        kind = req.get_param('kind')
        if kind == 'validation':
            TypeAdapter(int).validate_python('not-a-number')
        elif kind == 'auth':
            raise PermissionDenied(login='guest', permission='books.edit')
        elif kind == 'app':
            raise ProbeAppError(message='app failure')
        elif kind == 'domain':
            raise ProbeDomainError(message='domain failure')


class FakeUseCase:
    """Заглушка usecase: запоминает параметры, возвращает заданный результат"""

    def __init__(
        self, result: Any = None, error: Exception | None = None
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[Any, Any]] = []

    def run(self, params: Any, account: Any) -> Any:
        self.calls.append((params, account))
        if self.error is not None:
            raise self.error
        return self.result


class FakeQuery:
    """Заглушка запроса: запоминает параметры, возвращает заданный результат"""

    def __init__(
        self, result: Any = None, error: Exception | None = None
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[Any] = []

    def run(self, params: Any) -> Any:
        self.calls.append(params)
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def api_settings() -> ApiSettings:
    return ApiSettings(API_HOST='127.0.0.1', API_PORT=8080)


@pytest.fixture
def create_book_fake() -> Any:
    return FakeUseCase(result=1)


@pytest.fixture
def create_copies_fake() -> Any:
    return FakeUseCase(result=2)


@pytest.fixture
def create_catalog_book_fake() -> Any:
    return FakeUseCase(result=3)


@pytest.fixture
def register_reader_fake() -> Any:
    return FakeUseCase(result=4)


@pytest.fixture
def extend_membership_fake() -> Any:
    return FakeUseCase()


@pytest.fixture
def block_reader_fake() -> Any:
    return FakeUseCase()


@pytest.fixture
def unblock_reader_fake() -> Any:
    return FakeUseCase()


@pytest.fixture
def issue_loan_fake() -> Any:
    return FakeUseCase(result=5)


@pytest.fixture
def extend_loan_fake() -> Any:
    return FakeUseCase()


@pytest.fixture
def return_loan_fake() -> Any:
    return FakeUseCase()


@pytest.fixture
def find_books_fake() -> Any:
    return FakeQuery(
        result=[
            BookListItemDTO(
                id=1,
                isbn='9785171183660',
                title='Война и мир',
                authors=['Лев Толстой'],
                published_year=1869,
                available_copies=2,
            )
        ]
    )


@pytest.fixture
def get_book_fake() -> Any:
    return FakeQuery(
        result=BookCardDTO(
            id=1,
            isbn='9785171183660',
            title='Война и мир',
            authors=['Лев Толстой'],
            published_year=1869,
            copies=[
                BookCopyDTO(
                    id=5,
                    inventory_number='INV-001',
                    hall='Читальный зал',
                    rack=2,
                    shelf=3,
                    is_available=True,
                )
            ],
        )
    )


@pytest.fixture
def client(
    api_settings: ApiSettings,
    create_book_fake: Any,
    create_copies_fake: Any,
    register_reader_fake: Any,
    create_catalog_book_fake: Any,
    find_books_fake: Any,
    get_book_fake: Any,
    extend_membership_fake: Any,
    block_reader_fake: Any,
    unblock_reader_fake: Any,
    issue_loan_fake: Any,
    extend_loan_fake: Any,
    return_loan_fake: Any,
) -> testing.TestClient:
    app = create_app(
        api_settings,
        books=BooksResource(
            create_book=create_book_fake, find_books=find_books_fake
        ),
        copies=CopiesResource(add_copy=create_copies_fake),
        readers=ReadersResource(register_reader=register_reader_fake),
        book=BookResource(get_book=get_book_fake),
        catalog_books=CatalogBooksResource(
            create_book_from_catalog=create_catalog_book_fake
        ),
        memberships=MembershipsResource(
            extend_membership=extend_membership_fake
        ),
        reader_blocks=ReaderBlocksResource(
            block_reader=block_reader_fake, unblock_reader=unblock_reader_fake
        ),
        loans=LoansResource(issue_loan=issue_loan_fake),
        loan_extensions=LoanExtensionsResource(extend_loan=extend_loan_fake),
        returns=ReturnsResource(return_loan=return_loan_fake),
    )
    app.add_route('/probe', ProbeResource())
    return testing.TestClient(app)
