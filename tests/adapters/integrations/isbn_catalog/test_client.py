import pytest
from pytest_httpserver import HTTPServer

from library.app.commands.use_cases.books.create_book_from_catalog import (
    CatalogBook,
)
from library.integrations.isbn_catalog.client import (
    IsbnCatalogClient,
    IsbnCatalogUnavailable,
)
from library.integrations.isbn_catalog.settings import IsbnCatalogSettings

ISBN = '9785171183660'

PAYLOAD = {
    'isbn': ISBN,
    'title': 'Война и мир',
    'authors': ['Лев Толстой'],
    'year': 1869,
}


@pytest.fixture
def client(httpserver: HTTPServer) -> IsbnCatalogClient:
    return IsbnCatalogClient(
        IsbnCatalogSettings(
            ISBN_CATALOG_URL=httpserver.url_for('/'),
            ISBN_CATALOG_TIMEOUT=1.0,
        )
    )


def test_returns_catalog_book(
    client: IsbnCatalogClient, httpserver: HTTPServer
) -> None:
    httpserver.expect_oneshot_request(
        '/books', query_string={'isbn': ISBN}
    ).respond_with_json(PAYLOAD)

    book = client.find(ISBN)

    assert book == CatalogBook(
        isbn=ISBN,
        title='Война и мир',
        authors=['Лев Толстой'],
        year=1869,
    )
    assert len(httpserver.log) == 1
    request, _ = httpserver.log[0]
    assert request.path == '/books'
    assert request.args['isbn'] == ISBN


def test_missing_book_is_none(
    client: IsbnCatalogClient, httpserver: HTTPServer
) -> None:
    httpserver.expect_oneshot_request(
        '/books', query_string={'isbn': ISBN}
    ).respond_with_data(status=404)

    assert client.find(ISBN) is None


def test_server_error_is_unavailable(
    client: IsbnCatalogClient, httpserver: HTTPServer
) -> None:
    httpserver.expect_oneshot_request(
        '/books', query_string={'isbn': ISBN}
    ).respond_with_data('boom', status=500)

    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)


def test_invalid_json_is_unavailable(
    client: IsbnCatalogClient, httpserver: HTTPServer
) -> None:
    httpserver.expect_oneshot_request(
        '/books', query_string={'isbn': ISBN}
    ).respond_with_data('not a json', content_type='application/json')

    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)


def test_incomplete_payload_is_unavailable(
    client: IsbnCatalogClient, httpserver: HTTPServer
) -> None:
    httpserver.expect_oneshot_request(
        '/books', query_string={'isbn': ISBN}
    ).respond_with_json({'isbn': ISBN, 'authors': ['Лев Толстой']})

    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)


def test_network_error_is_unavailable() -> None:
    client = IsbnCatalogClient(
        IsbnCatalogSettings(
            ISBN_CATALOG_URL='http://127.0.0.1:9/',
            ISBN_CATALOG_TIMEOUT=0.2,
        )
    )

    with pytest.raises(IsbnCatalogUnavailable):
        client.find(ISBN)
