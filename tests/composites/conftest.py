import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from falcon import testing
from pytest_httpserver import HTTPServer

from library.infra.db.settings import TestDBSettings

AUTH_HEADERS = {'X-User': 'admin'}


@dataclass
class CreatedRecords:
    books: list[int] = field(default_factory=list[int])
    readers: list[int] = field(default_factory=list[int])
    notifications_after: int = 0


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
    users = [
        {
            'login': 'admin',
            'permissions': [
                'books.edit',
                'readers.edit',
                'loans.edit',
            ],
        },
    ]
    with pytest.MonkeyPatch.context() as env:
        env.setenv('DB_HOST', test_db_settings.DB_HOST)
        env.setenv('DB_PORT', str(test_db_settings.DB_PORT))
        env.setenv('DB_USER', test_db_settings.DB_USER)
        env.setenv('DB_PASS', test_db_settings.DB_PASS)
        env.setenv('DB_NAME', test_db_settings.DB_NAME)
        env.setenv('API_HOST', '127.0.0.1')
        env.setenv('API_PORT', '8090')
        env.setenv('ISBN_CATALOG_URL', catalog_server.url_for('/'))
        env.setenv('USERS', json.dumps(users))
        yield


@pytest.fixture(scope='session')
def api_app(test_env: None) -> Any:
    # Импорт композита читает настройки из окружения, подготовленного test_env.
    from library.composites.interfaces.api.wsgi import app  # noqa: PLC0415

    return app


@pytest.fixture
def api_client(api_app: Any) -> testing.TestClient:
    return testing.TestClient(api_app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return dict(AUTH_HEADERS)


@pytest.fixture
def catalog(catalog_server: HTTPServer) -> Iterator[HTTPServer]:
    yield catalog_server
    catalog_server.clear()


@pytest.fixture
def created_records(raw_db: Any) -> Iterator[CreatedRecords]:
    records = CreatedRecords(
        notifications_after=int(
            raw_db.scalar(
                'SELECT coalesce(max(id), 0) FROM library.notifications',
            ),
        ),
    )
    yield records
    for reader_id in records.readers:
        raw_db.execute(
            'DELETE FROM library.readers WHERE id = %(id)s',
            id=reader_id,
        )
    for book_id in records.books:
        raw_db.execute(
            'DELETE FROM library.books WHERE id = %(id)s',
            id=book_id,
        )
    raw_db.execute(
        'DELETE FROM library.notifications WHERE id > %(id)s',
        id=records.notifications_after,
    )


@pytest.fixture
def create_book(
    api_client: testing.TestClient,
    created_records: CreatedRecords,
) -> Callable[..., int]:
    def create(**overrides: Any) -> int:
        payload: dict[str, Any] = {
            'isbn': '9780132350884',
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'published_year': 2008,
        }
        payload.update(overrides)
        response = api_client.simulate_post(
            '/library/books',
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 201
        book_id = int(response.json['id'])
        created_records.books.append(book_id)
        return book_id

    return create


@pytest.fixture
def create_reader(
    api_client: testing.TestClient,
    created_records: CreatedRecords,
) -> Callable[..., int]:
    def create(**overrides: Any) -> int:
        payload: dict[str, Any] = {
            'full_name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'phone': '+79990000000',
            'tier': 'basic',
            'valid_until': '2027-01-01',
        }
        payload.update(overrides)
        response = api_client.simulate_post(
            '/library/readers',
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 201
        reader_id = int(response.json['id'])
        created_records.readers.append(reader_id)
        return reader_id

    return create


@pytest.fixture
def add_copy(api_client: testing.TestClient) -> Callable[..., None]:
    def add(
        book_id: int,
        inventory_number: str = 'INV-1',
        **overrides: Any,
    ) -> None:
        payload: dict[str, Any] = {
            'book_id': book_id,
            'inventory_number': inventory_number,
            'hall': 'A',
            'rack': 1,
            'shelf': 1,
        }
        payload.update(overrides)
        response = api_client.simulate_post(
            '/library/copies',
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200

    return add


@pytest.fixture
def issue_loan(api_client: testing.TestClient) -> Callable[..., int]:
    def issue(
        reader_id: int,
        book_id: int,
        inventory_number: str = 'INV-1',
    ) -> int:
        response = api_client.simulate_post(
            '/library/loans',
            json={
                'reader_id': reader_id,
                'book_id': book_id,
                'inventory_number': inventory_number,
            },
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 201
        return int(response.json['id'])

    return issue
