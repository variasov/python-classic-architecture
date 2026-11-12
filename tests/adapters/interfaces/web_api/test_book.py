from typing import Any

from falcon import testing

from library.app.queries.books.get_book import GetBookNotFound

CARD = {
    'id': 1,
    'isbn': '9785171183660',
    'title': 'Война и мир',
    'authors': ['Лев Толстой'],
    'published_year': 1869,
    'copies': [
        {
            'id': 5,
            'inventory_number': 'INV-001',
            'hall': 'Читальный зал',
            'rack': 2,
            'shelf': 3,
            'is_available': True,
        },
    ],
}


def test_book_card_returns_200(
    client: testing.TestClient,
    get_book_fake: Any,
) -> None:
    response = client.simulate_get('/library/book', params={'id': '1'})

    assert response.status_code == 200
    assert response.json == CARD
    assert get_book_fake.calls == [{'id': '1'}]


def test_missing_book_is_422(
    client: testing.TestClient,
    get_book_fake: Any,
) -> None:
    get_book_fake.error = GetBookNotFound(id=404)

    response = client.simulate_get('/library/book', params={'id': '404'})

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'GetBookNotFound'
    assert detail['ctx'] == {'id': 404}
