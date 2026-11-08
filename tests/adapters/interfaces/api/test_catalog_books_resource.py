import json

from library.app.commands.domain.book import BookNotInCatalog


def test_catalog_books_post_creates_book(api) -> None:
    api.create_book_from_catalog.result = 3
    response = api.client.simulate_post(
        '/library/catalog_books',
        json={'isbn': '9780132350884'},
    )
    assert response.status_code == 201
    assert response.json == {'id': 3}
    params = api.create_book_from_catalog.calls[0][1]
    assert params.isbn == '9780132350884'


def test_catalog_books_post_missing_in_catalog(api) -> None:
    api.create_book_from_catalog.error = BookNotInCatalog(
        isbn='9780132350884',
    )
    response = api.client.simulate_post(
        '/library/catalog_books',
        json={'isbn': '9780132350884'},
    )
    assert response.status_code == 422
    body = json.loads(response.text)
    assert body[0]['type'] == 'BookNotInCatalog'


def test_catalog_books_post_validation(api) -> None:
    response = api.client.simulate_post(
        '/library/catalog_books',
        json={},
    )
    assert response.status_code == 400
