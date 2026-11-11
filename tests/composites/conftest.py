from collections.abc import Iterator
from typing import Any

import falcon
import pytest
from falcon import testing


@pytest.fixture(scope='session')
def test_env(migrated_db: object) -> Iterator[None]:
    """Настройки API уже пришли из окружения запуска тестов"""
    yield


@pytest.fixture(scope='session')
def api_app(test_env: None) -> falcon.App[Any, Any]:
    from library.composites.interfaces.api import wsgi

    return wsgi.app


@pytest.fixture
def client(api_app: falcon.App[Any, Any]) -> testing.TestClient:
    return testing.TestClient(api_app)
