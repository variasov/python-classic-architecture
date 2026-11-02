import json

import pytest
from library.integrations.isbn_catalog.client import (
    IsbnCatalogClient,
    IsbnCatalogUnavailable,
)
from library.integrations.isbn_catalog.settings import IsbnCatalogSettings
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from tests.conftest import ISBN


@pytest.fixture
def client(httpserver: HTTPServer) -> IsbnCatalogClient:
    return IsbnCatalogClient(
        settings=IsbnCatalogSettings(ISBN_CATALOG_URL=httpserver.url_for('/')),
    )


def test_find_translates_response_to_dto(
    client: IsbnCatalogClient,
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request('/books', query_string={'isbn': ISBN}).respond_with_json(
        {'isbn': ISBN, 'title': 'Т', 'authors': ['А', 'Б'], 'year': 1869, 'extra': 1},
    )
    book = client.find(ISBN)
    assert book is not None
    assert (book.isbn, book.title, book.authors, book.year) == (
        ISBN,
        'Т',
        ['А', 'Б'],
        1869,
    )


def test_sends_isbn_in_query(client: IsbnCatalogClient, httpserver: HTTPServer) -> None:
    seen: list[str] = []

    def handler(request: Request) -> Response:
        seen.append(request.args['isbn'])
        return Response(
            json.dumps({'isbn': ISBN, 'title': 'T', 'authors': [], 'year': 1}),
            content_type='application/json',
        )

    httpserver.expect_request('/books').respond_with_handler(handler)
    client.find(ISBN)
    assert seen == [ISBN]


def test_not_found_is_none(client: IsbnCatalogClient, httpserver: HTTPServer) -> None:
    httpserver.expect_request('/books').respond_with_data(status=404)
    assert client.find(ISBN) is None


@pytest.mark.parametrize('status', [500, 503, 400])
def test_http_errors_raise(
    client: IsbnCatalogClient,
    httpserver: HTTPServer,
    status: int,
) -> None:
    httpserver.expect_request('/books').respond_with_data(status=status)
    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)


@pytest.mark.parametrize(
    'payload',
    [{'isbn': ISBN}, {'isbn': ISBN, 'title': 'T', 'authors': 'x', 'year': 'abc'}, []],
)
def test_invalid_response_raises(
    client: IsbnCatalogClient,
    httpserver: HTTPServer,
    payload: object,
) -> None:
    httpserver.expect_request('/books').respond_with_json(payload)
    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)


def test_non_json_response_raises(
    client: IsbnCatalogClient,
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request('/books').respond_with_data('<html>')
    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)


def test_unreachable_server_raises() -> None:
    client = IsbnCatalogClient(
        settings=IsbnCatalogSettings(
            ISBN_CATALOG_URL='http://127.0.0.1:1',
            ISBN_CATALOG_TIMEOUT=1,
        ),
    )
    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)
