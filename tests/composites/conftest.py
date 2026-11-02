import json
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from falcon.testing import TestClient
from library.infra.db.settings import TestDBSettings
from pytest_httpserver import HTTPServer

from tests.conftest import FULL_ACCESS, RawDb

ADMIN = {'X-User': 'admin'}


@pytest.fixture(scope='session')
def catalog_server() -> Iterator[HTTPServer]:
    server = HTTPServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope='session')
def test_env(
    test_db_settings: TestDBSettings,
    migrated_db: None,
    catalog_server: HTTPServer,
) -> Iterator[None]:
    with pytest.MonkeyPatch.context() as env:
        env.setenv('DB_HOST', test_db_settings.DB_HOST)
        env.setenv('DB_PORT', str(test_db_settings.DB_PORT))
        env.setenv('DB_NAME', test_db_settings.DB_NAME)
        env.setenv('DB_USER', test_db_settings.DB_USER)
        env.setenv('DB_PASS', test_db_settings.DB_PASS)
        env.setenv('ISBN_CATALOG_URL', catalog_server.url_for('/'))
        env.setenv('API_USERS', json.dumps({'admin': sorted(FULL_ACCESS), 'guest': []}))
        yield


@pytest.fixture(scope='session')
def api_client(test_env: None) -> TestClient:
    from library.composites.interfaces.api.wsgi import app  # noqa: PLC0415

    return TestClient(app)


@pytest.fixture
def created(raw_db: RawDb) -> Iterator[dict[str, list[int]]]:
    """Корни агрегатов, созданные тестом через API; удаляются после теста."""
    ids: dict[str, list[int]] = {'books': [], 'readers': []}
    yield ids
    raw_db.execute(
        'DELETE FROM library.books WHERE id = ANY(%(ids)s)',
        ids=ids['books'],
    )
    raw_db.execute(
        'DELETE FROM library.readers WHERE id = ANY(%(ids)s)',
        ids=ids['readers'],
    )


@pytest.fixture
def create_book(
    api_client: TestClient,
    created: dict[str, list[int]],
) -> Callable[..., int]:
    def factory(copies: int = 1, **overrides: Any) -> int:
        body: dict[str, Any] = {
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Толстой'],
            'published_year': 1869,
            **overrides,
        }
        response = api_client.simulate_post('/library/books', json=body, headers=ADMIN)
        assert response.status_code == 201
        book_id: int = response.json['id']
        created['books'].append(book_id)
        for number in range(copies):
            copy = {
                'book_id': book_id,
                'inventory_number': f'INV-{number}',
                'hall': 'A',
                'rack': 1,
                'shelf': 1,
            }
            added = api_client.simulate_post(
                '/library/copies',
                json=copy,
                headers=ADMIN,
            )
            assert added.status_code == 200
        return book_id

    return factory


@pytest.fixture
def register_reader(
    api_client: TestClient,
    created: dict[str, list[int]],
) -> Callable[..., int]:
    def factory(**overrides: Any) -> int:
        body: dict[str, Any] = {
            'full_name': 'Иван Иванов',
            'email': 'i@example.com',
            'tier': 'basic',
            'valid_until': '2099-01-01',
            **overrides,
        }
        response = api_client.simulate_post(
            '/library/readers',
            json=body,
            headers=ADMIN,
        )
        assert response.status_code == 201
        reader_id: int = response.json['id']
        created['readers'].append(reader_id)
        return reader_id

    return factory
