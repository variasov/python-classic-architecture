import json

from library.app.queries.books.get_book import (
    CopyDTO,
    GetBookDTO,
    GetBookNotFound,
)


def test_book_get_returns_card(api) -> None:
    api.get_book.result = GetBookDTO(
        id=1,
        isbn='9780132350884',
        title='Clean Code',
        authors=['Robert Martin'],
        published_year=2008,
        copies=[
            CopyDTO(
                inventory_number='INV-1',
                hall='A',
                rack=1,
                shelf=2,
                is_available=True,
            ),
        ],
    )
    response = api.client.simulate_get(
        '/library/book',
        params={'id': '1'},
    )
    assert response.status_code == 200
    body = response.json
    assert body['id'] == 1
    assert body['copies'][0]['inventory_number'] == 'INV-1'
    assert api.get_book.calls[0][0].id == 1


def test_book_get_not_found(api) -> None:
    api.get_book.error = GetBookNotFound(id=42)
    response = api.client.simulate_get(
        '/library/book',
        params={'id': '42'},
    )
    assert response.status_code == 422
    body = json.loads(response.text)
    assert body[0]['type'] == 'GetBookNotFound'
    assert body[0]['ctx'] == {'id': 42}


def test_book_get_invalid_id(api) -> None:
    response = api.client.simulate_get(
        '/library/book',
        params={'id': 'not-a-number'},
    )
    assert response.status_code == 400
