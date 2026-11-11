from collections.abc import Iterator
from typing import Any

import falcon
import pytest
from falcon import testing
from pytest_httpserver import HTTPServer


@pytest.fixture(scope='session')
def catalog_server() -> Iterator[HTTPServer]:
    server = HTTPServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope='session')
def test_env(
    migrated_db: object,
    catalog_server: HTTPServer,
) -> Iterator[None]:
    """Настройки API пришли из окружения, адрес каталога даёт stub-сервер"""
    with pytest.MonkeyPatch.context() as env:
        env.setenv('ISBN_CATALOG_URL', catalog_server.url_for('/'))
        yield


@pytest.fixture(scope='session')
def api_app(test_env: None) -> falcon.App[Any, Any]:
    from library.composites.interfaces.api import wsgi

    return wsgi.app


@pytest.fixture
def client(api_app: falcon.App[Any, Any]) -> testing.TestClient:
    return testing.TestClient(api_app)
