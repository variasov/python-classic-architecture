from datetime import date
from typing import Any

import pytest
from falcon.testing import TestClient
from library.app.commands.domain.book import BookNotFound
from library.app.commands.use_cases.books.create_book import CreateBookParams
from library.app.commands.use_cases.loans.issue_loan_command import (
    IssueLoanCommandParams,
)
from library.app.commands.use_cases.readers.register_reader import (
    RegisterReaderParams,
)
from library.app.queries.books.find_books import FindBooksParams, FoundBook
from library.app.queries.books.get_book import (
    BookCard,
    CopyCard,
    GetBookNotFound,
    GetBookParams,
    ShelfCard,
)
from library.app.roles import PermissionDenied

from tests.adapters.interfaces.api.conftest import FakeUseCase

ADMIN = {'X-User': 'admin'}


def test_find_books_parses_query_and_serializes(
    client: TestClient,
    find_books: FakeUseCase,
) -> None:
    find_books.result = [
        FoundBook(
            id=1,
            isbn='9785171183660',
            title='T',
            authors=['A'],
            published_year=2000,
            available_copies=2,
        ),
    ]
    response = client.simulate_get(
        '/library/books',
        params={'title__contains': 'abc', 'only_available': 'true', 'limit': '5'},
    )
    assert response.status_code == 200
    assert response.json[0]['available_copies'] == 2
    assert find_books.calls == [
        (FindBooksParams(title__contains='abc', only_available=True, limit=5),),
    ]


@pytest.mark.parametrize(
    'params',
    [{'title__contains': 'ab'}, {'limit': '0'}, {'limit': 'x'}, {'order_by': 'zzz'}],
)
def test_find_books_invalid_query_is_400(
    client: TestClient,
    find_books: FakeUseCase,
    params: dict[str, str],
) -> None:
    response = client.simulate_get('/library/books', params=params)
    assert response.status_code == 400
    assert find_books.calls == []


def test_create_book_returns_201_with_id(
    client: TestClient,
    create_book: FakeUseCase,
) -> None:
    body: dict[str, Any] = {
        'isbn': '9785171183660',
        'title': 'T',
        'authors': ['A'],
        'published_year': 2000,
    }
    response = client.simulate_post('/library/books', json=body, headers=ADMIN)
    assert response.status_code == 201
    assert response.json == {'id': 1}
    params, account = create_book.calls[0]
    assert params == CreateBookParams(**body)
    assert account.login == 'admin'
    assert 'books.edit' in account.permissions


@pytest.mark.parametrize(
    'body',
    [{'title': 'T'}, {'isbn': '1', 'title': 'T', 'authors': None, 'published_year': 1}],
)
def test_create_book_invalid_body_is_400(
    client: TestClient,
    create_book: FakeUseCase,
    body: dict[str, object],
) -> None:
    response = client.simulate_post('/library/books', json=body, headers=ADMIN)
    assert response.status_code == 400
    assert create_book.calls == []


def test_app_error_is_422_with_type_and_ctx(
    client: TestClient,
    create_book: FakeUseCase,
) -> None:
    create_book.error = PermissionDenied(login='guest', permission='books.edit')
    body: dict[str, Any] = {
        'isbn': '9785171183660',
        'title': 'T',
        'authors': [],
        'published_year': 2000,
    }
    response = client.simulate_post('/library/books', json=body)
    assert response.status_code == 422
    assert response.json[0]['type'] == 'PermissionDenied'
    assert response.json[0]['ctx'] == {'login': 'guest', 'permission': 'books.edit'}


def test_domain_error_is_422(client: TestClient, create_book: FakeUseCase) -> None:
    create_book.error = BookNotFound(id=4)
    body: dict[str, Any] = {
        'isbn': '9785171183660',
        'title': 'T',
        'authors': [],
        'published_year': 2000,
    }
    response = client.simulate_post('/library/books', json=body)
    assert response.status_code == 422
    assert response.json[0]['type'] == 'BookNotFound'
    assert response.json[0]['ctx'] == {'id': 4}


def test_get_book(client: TestClient, get_book: FakeUseCase) -> None:
    get_book.result = BookCard(
        id=1,
        isbn='9785171183660',
        title='T',
        authors=['A'],
        published_year=2000,
        copies=[
            CopyCard(
                inventory_number='1',
                is_available=True,
                shelf=ShelfCard(hall='A', rack=1, shelf=2),
            ),
        ],
    )
    response = client.simulate_get('/library/book', params={'id': '1'})
    assert response.status_code == 200
    assert response.json['copies'][0]['shelf'] == {'hall': 'A', 'rack': 1, 'shelf': 2}
    assert get_book.calls == [(GetBookParams(id=1),)]


def test_get_book_not_found_is_422(client: TestClient, get_book: FakeUseCase) -> None:
    get_book.error = GetBookNotFound(id=7)
    response = client.simulate_get('/library/book', params={'id': '7'})
    assert response.status_code == 422
    assert response.json[0]['type'] == 'GetBookNotFound'


def test_get_book_without_id_is_400(client: TestClient, get_book: FakeUseCase) -> None:
    assert client.simulate_get('/library/book').status_code == 400
    assert get_book.calls == []


def test_register_reader_parses_date(
    client: TestClient,
    register_reader: FakeUseCase,
) -> None:
    body: dict[str, Any] = {
        'full_name': 'И',
        'email': 'a@b',
        'tier': 'basic',
        'valid_until': '2026-12-31',
    }
    response = client.simulate_post('/library/readers', json=body, headers=ADMIN)
    assert response.status_code == 201
    assert response.json == {'id': 3}
    assert register_reader.calls[0][0] == RegisterReaderParams(
        full_name='И',
        email='a@b',
        tier='basic',
        valid_until=date(2026, 12, 31),
    )


def test_register_reader_bad_date_is_400(client: TestClient) -> None:
    body: dict[str, Any] = {
        'full_name': 'И',
        'email': 'a@b',
        'tier': 'basic',
        'valid_until': 'вчера',
    }
    assert client.simulate_post('/library/readers', json=body).status_code == 400


def test_find_readers(client: TestClient, find_readers: FakeUseCase) -> None:
    response = client.simulate_get('/library/readers', params={'limit': '3'})
    assert response.status_code == 200
    assert response.json == []
    assert find_readers.calls[0][0].limit == 3


def test_extend_membership_returns_200(
    client: TestClient,
    extend_membership: FakeUseCase,
) -> None:
    body: dict[str, Any] = {'reader_id': 1, 'until': '2027-01-01'}
    response = client.simulate_put('/library/memberships', json=body, headers=ADMIN)
    assert response.status_code == 200
    assert extend_membership.calls[0][0].until == date(2027, 1, 1)


def test_issue_loan_returns_201_with_id(
    client: TestClient,
    issue_loan: FakeUseCase,
) -> None:
    body: dict[str, Any] = {
        'reader_id': 1,
        'book_id': 2,
        'inventory_number': 'X',
        'days': 7,
    }
    response = client.simulate_post('/library/loans', json=body, headers=ADMIN)
    assert response.status_code == 201
    assert response.json == {'id': 5}
    assert issue_loan.calls[0][0] == IssueLoanCommandParams(**body)


def test_issue_loan_value_error_from_params_is_400(
    client: TestClient,
    issue_loan: FakeUseCase,
) -> None:
    body: dict[str, Any] = {
        'reader_id': 1,
        'book_id': 2,
        'inventory_number': 'X',
        'days': 1000,
    }
    assert client.simulate_post('/library/loans', json=body).status_code == 400
    assert issue_loan.calls == []


def test_find_loans(client: TestClient, find_loans: FakeUseCase) -> None:
    response = client.simulate_get(
        '/library/loans',
        params={'reader_id': '4', 'only_overdue': 'true'},
    )
    assert response.status_code == 200
    params = find_loans.calls[0][0]
    assert (params.reader_id, params.only_overdue) == (4, True)


@pytest.mark.parametrize(
    ('path', 'fixture_name', 'body'),
    [
        ('/library/loan_extensions', 'extend_loan', {'loan_id': 1, 'days': 3}),
        ('/library/returns', 'return_loan', {'loan_id': 1}),
        ('/library/reader_blocks', 'block_reader', {'reader_id': 1}),
        (
            '/library/copies',
            'add_copy',
            {'book_id': 1, 'inventory_number': 'X', 'hall': 'A', 'rack': 1, 'shelf': 1},
        ),
    ],
)
def test_actions_on_existing_aggregates_return_200(
    client: TestClient,
    request: pytest.FixtureRequest,
    path: str,
    fixture_name: str,
    body: dict[str, object],
) -> None:
    use_case: FakeUseCase = request.getfixturevalue(fixture_name)
    response = client.simulate_post(path, json=body, headers=ADMIN)
    assert response.status_code == 200
    assert len(use_case.calls) == 1


def test_create_from_catalog_returns_201(
    client: TestClient,
    create_from_catalog: FakeUseCase,
) -> None:
    response = client.simulate_post(
        '/library/catalog_books',
        json={'isbn': '9785171183660'},
        headers=ADMIN,
    )
    assert response.status_code == 201
    assert response.json == {'id': 9}


def test_unknown_user_is_anonymous_without_permissions(
    client: TestClient,
    create_book: FakeUseCase,
) -> None:
    body: dict[str, Any] = {
        'isbn': '9785171183660',
        'title': 'T',
        'authors': [],
        'published_year': 2000,
    }
    client.simulate_post('/library/books', json=body, headers={'X-User': 'stranger'})
    account = create_book.calls[0][1]
    assert (account.login, account.permissions) == ('stranger', frozenset())
