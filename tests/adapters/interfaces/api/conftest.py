import json
from dataclasses import dataclass
from typing import Any

import falcon
import pytest
from falcon import testing
from pydantic import TypeAdapter

from library.app.commands.domain.errors import DomainError
from library.app.errors import AppError
from library.app.roles import PermissionDenied
from library.composites.interfaces.api.wsgi import create_app
from library.interfaces.api.resources.books import BooksResource
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


@pytest.fixture
def api_settings() -> ApiSettings:
    return ApiSettings(API_HOST='127.0.0.1', API_PORT=8080)


@pytest.fixture
def create_book_fake() -> Any:
    return FakeUseCase(result=1)


@pytest.fixture
def client(
    api_settings: ApiSettings, create_book_fake: Any
) -> testing.TestClient:
    app = create_app(
        api_settings, books=BooksResource(create_book=create_book_fake)
    )
    app.add_route('/probe', ProbeResource())
    return testing.TestClient(app)
