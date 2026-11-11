from typing import Any

from falcon import testing

from library.app.commands.use_cases.books.create_book import CreateBookParams
from library.app.roles import PermissionDenied


def test_create_book_returns_201_and_id(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json={
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Лев Толстой'],
            'published_year': 1869,
        },
    )

    assert response.status_code == 201
    assert response.json == {'id': 1}


def test_request_body_is_parsed_into_params(
    client: testing.TestClient, create_book_fake: Any
) -> None:
    client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json={
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Лев Толстой'],
            'published_year': 1869,
        },
    )

    params, account = create_book_fake.calls[0]
    assert params == CreateBookParams(
        isbn='9785171183660',
        title='Война и мир',
        authors=['Лев Толстой'],
        published_year=1869,
    )
    assert account.login == 'admin'


def test_invalid_body_is_400(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json={'isbn': '9785171183660', 'authors': ['Лев Толстой']},
    )

    assert response.status_code == 400


def test_permission_denied_is_403(
    client: testing.TestClient, create_book_fake: Any
) -> None:
    create_book_fake.error = PermissionDenied(login='guest', permission='books.edit')

    response = client.simulate_post(
        '/library/books',
        headers={'X-User': 'guest'},
        json={
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Лев Толстой'],
            'published_year': 1869,
        },
    )

    assert response.status_code == 403
