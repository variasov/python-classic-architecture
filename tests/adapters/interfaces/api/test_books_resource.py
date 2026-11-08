import json

from library.app.queries.books.find_books import BookDTO
from library.app.roles import PermissionDenied


def test_books_get_parses_query(api) -> None:
    api.find_books.result = [
        BookDTO(
            id=1,
            isbn='9780132350884',
            title='Clean Code',
            authors=['Robert Martin'],
            published_year=2008,
        ),
    ]
    response = api.client.simulate_get(
        '/library/books',
        params={'title__contains': 'Clean', 'limit': '5'},
    )
    assert response.status_code == 200
    assert response.json == [
        {
            'id': 1,
            'isbn': '9780132350884',
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'published_year': 2008,
        },
    ]
    params = api.find_books.calls[0][0]
    assert params.title__contains == 'Clean'
    assert params.limit == 5


def test_books_get_rejects_invalid_query(api) -> None:
    response = api.client.simulate_get(
        '/library/books',
        params={'limit': '0'},
    )
    assert response.status_code == 400
    assert api.find_books.calls == []


def test_books_post_creates_book(api) -> None:
    api.create_book.result = 7
    response = api.client.simulate_post(
        '/library/books',
        json={
            'isbn': '9780132350884',
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'published_year': 2008,
        },
    )
    assert response.status_code == 201
    assert response.json == {'id': 7}
    account, params, _ = api.create_book.calls[0]
    assert params.isbn == '9780132350884'
    assert account.login == ''


def test_books_post_validation_error(api) -> None:
    response = api.client.simulate_post(
        '/library/books',
        json={'isbn': '9780132350884'},
    )
    assert response.status_code == 400
    assert api.create_book.calls == []


def test_books_post_application_error(api) -> None:
    api.create_book.error = PermissionDenied(
        login='guest',
        permission='books.edit',
    )
    response = api.client.simulate_post(
        '/library/books',
        json={
            'isbn': '9780132350884',
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'published_year': 2008,
        },
    )
    assert response.status_code == 422
    body = json.loads(response.text)
    assert body[0]['type'] == 'PermissionDenied'
    assert body[0]['ctx'] == {'login': 'guest', 'permission': 'books.edit'}
