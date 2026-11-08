import pytest

from library.integrations.isbn_catalog.client import (
    IsbnCatalogClient,
    IsbnCatalogInvalidResponse,
    IsbnCatalogUnavailable,
)
from library.integrations.isbn_catalog.settings import IsbnCatalogSettings


def _client(httpserver) -> IsbnCatalogClient:
    return IsbnCatalogClient(
        settings=IsbnCatalogSettings(
            ISBN_CATALOG_URL=httpserver.url_for('/'),
        ),
    )


def test_find_returns_catalog_book(httpserver) -> None:
    httpserver.expect_request(
        '/books',
        query_string={'isbn': '9780132350884'},
    ).respond_with_json(
        {
            'isbn': '9780132350884',
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'year': 2008,
            'unknown': 'ignored',
        },
    )
    book = _client(httpserver).find('9780132350884')
    assert book is not None
    assert book.isbn == '9780132350884'
    assert book.title == 'Clean Code'
    assert book.authors == ['Robert Martin']
    assert book.year == 2008


def test_find_returns_none_on_404(httpserver) -> None:
    httpserver.expect_request(
        '/books',
        query_string={'isbn': '9780132350884'},
    ).respond_with_data(status=404)
    assert _client(httpserver).find('9780132350884') is None


def test_find_raises_on_server_error(httpserver) -> None:
    httpserver.expect_request(
        '/books',
        query_string={'isbn': '9780132350884'},
    ).respond_with_data(status=500)
    with pytest.raises(IsbnCatalogUnavailable):
        _client(httpserver).find('9780132350884')


def test_find_raises_on_invalid_response(httpserver) -> None:
    httpserver.expect_request(
        '/books',
        query_string={'isbn': '9780132350884'},
    ).respond_with_json({'isbn': '9780132350884'})
    with pytest.raises(IsbnCatalogInvalidResponse):
        _client(httpserver).find('9780132350884')


def test_find_sends_isbn(httpserver) -> None:
    httpserver.expect_request(
        '/books',
        query_string={'isbn': '9780132350884'},
    ).respond_with_json(
        {
            'isbn': '9780132350884',
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'year': 2008,
        },
    )
    _client(httpserver).find('9780132350884')
    assert len(httpserver.log) == 1
    request, _response = httpserver.log[0]
    assert request.args['isbn'] == '9780132350884'
