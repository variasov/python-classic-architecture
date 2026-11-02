from collections.abc import Callable
from typing import Any

import pytest
from classic.signals import Hub
from falcon.testing import TestClient
from library.app.commands.signals import LoanIssued
from pytest_httpserver import HTTPServer

from tests.composites.conftest import ADMIN
from tests.conftest import ISBN, OTHER_ISBN, RawDb


def issue(
    client: TestClient,
    reader_id: int,
    book_id: int,
    inventory_number: str = 'INV-0',
) -> Any:
    body: dict[str, Any] = {
        'reader_id': reader_id,
        'book_id': book_id,
        'inventory_number': inventory_number,
    }
    return client.simulate_post('/library/loans', json=body, headers=ADMIN)


def test_books_create_find_and_card(
    api_client: TestClient,
    create_book: Callable[..., int],
) -> None:
    book_id = create_book(copies=2, title='Уникальнейшая книга')
    found = api_client.simulate_get(
        '/library/books',
        params={'title__contains': 'Уникальнейшая'},
    )
    assert [b['id'] for b in found.json] == [book_id]
    assert found.json[0]['available_copies'] == 2
    card = api_client.simulate_get('/library/book', params={'id': str(book_id)})
    assert [c['inventory_number'] for c in card.json['copies']] == ['INV-0', 'INV-1']


def test_book_not_found_is_422(api_client: TestClient) -> None:
    response = api_client.simulate_get('/library/book', params={'id': '-1'})
    assert response.status_code == 422
    assert response.json[0]['type'] == 'GetBookNotFound'


def test_permission_denied_is_422(api_client: TestClient) -> None:
    body: dict[str, Any] = {
        'isbn': ISBN,
        'title': 'T',
        'authors': [],
        'published_year': 2000,
    }
    response = api_client.simulate_post(
        '/library/books',
        json=body,
        headers={'X-User': 'guest'},
    )
    assert response.status_code == 422
    assert response.json[0]['type'] == 'PermissionDenied'


def test_validation_error_is_400(api_client: TestClient) -> None:
    response = api_client.simulate_get(
        '/library/books',
        params={'title__contains': 'ab'},
    )
    assert response.status_code == 400


def test_domain_error_is_422(api_client: TestClient) -> None:
    body: dict[str, Any] = {
        'isbn': '123',
        'title': 'T',
        'authors': [],
        'published_year': 2000,
    }
    response = api_client.simulate_post('/library/books', json=body, headers=ADMIN)
    assert response.status_code == 422
    assert response.json[0]['type'] == 'InvalidIsbn'


def test_readers_membership_block_and_find(
    api_client: TestClient,
    register_reader: Callable[..., int],
) -> None:
    reader_id = register_reader()
    extended = api_client.simulate_put(
        '/library/memberships',
        json={'reader_id': reader_id, 'until': '2100-01-01'},
        headers=ADMIN,
    )
    assert extended.status_code == 200
    blocked = api_client.simulate_post(
        '/library/reader_blocks',
        json={'reader_id': reader_id},
        headers=ADMIN,
    )
    assert blocked.status_code == 200
    readers = api_client.simulate_get('/library/readers', params={'limit': '100'}).json
    mine = next(r for r in readers if r['id'] == reader_id)
    assert (mine['valid_until'], mine['is_blocked']) == ('2100-01-01', True)


def test_loan_lifecycle_with_notification(
    api_client: TestClient,
    create_book: Callable[..., int],
    register_reader: Callable[..., int],
    raw_db: RawDb,
) -> None:
    book_id, reader_id = create_book(), register_reader()
    created = issue(api_client, reader_id, book_id)
    assert created.status_code == 201
    loan_id = created.json['id']
    kind = raw_db.scalar(
        'SELECT kind FROM library.notifications WHERE loan_id = %(id)s',
        id=loan_id,
    )
    assert kind == 'loan_issued'
    extended = api_client.simulate_post(
        '/library/loan_extensions',
        json={'loan_id': loan_id, 'days': 3},
        headers=ADMIN,
    )
    assert extended.status_code == 200
    active = api_client.simulate_get(
        '/library/loans',
        params={'reader_id': str(reader_id), 'only_active': 'true'},
    )
    assert [x['extensions_count'] for x in active.json] == [1]
    returned = api_client.simulate_post(
        '/library/returns',
        json={'loan_id': loan_id},
        headers=ADMIN,
    )
    assert returned.status_code == 200
    again = api_client.simulate_post(
        '/library/returns',
        json={'loan_id': loan_id},
        headers=ADMIN,
    )
    assert again.json[0]['type'] == 'LoanAlreadyReturned'
    assert (
        api_client.simulate_get(
            '/library/loans',
            params={'reader_id': str(reader_id), 'only_active': 'true'},
        ).json
        == []
    )


def test_transaction_rolls_back_on_failure(
    api_client: TestClient,
    create_book: Callable[..., int],
    register_reader: Callable[..., int],
    raw_db: RawDb,
) -> None:
    from library.composites.app.hub import hub  # noqa: PLC0415

    def boom(signal: LoanIssued) -> None:
        raise RuntimeError

    book_id, reader_id = create_book(), register_reader()
    hub.add_reaction(LoanIssued, boom)
    try:
        response = issue(api_client, reader_id, book_id)
    finally:
        hub.remove_reaction(LoanIssued, boom)
    assert response.status_code == 500
    assert (
        raw_db.scalar(
            'SELECT count(*) FROM library.loans WHERE reader_id = %(id)s',
            id=reader_id,
        )
        == 0
    )
    assert (
        raw_db.scalar(
            'SELECT count(*) FROM library.notifications WHERE reader_id = %(id)s',
            id=reader_id,
        )
        == 0
    )
    assert (
        raw_db.scalar(
            'SELECT is_available FROM library.copies WHERE book_id = %(id)s',
            id=book_id,
        )
        is True
    )


def test_signal_subscribers_registered_in_api_process(api_client: TestClient) -> None:
    from library.composites.app.hub import hub  # noqa: PLC0415

    assert isinstance(hub, Hub)
    assert LoanIssued in hub._reactions
    assert len(hub._reactions[LoanIssued]) >= 1


def test_catalog_integration_and_retry(
    api_client: TestClient,
    catalog_server: HTTPServer,
    created: dict[str, list[int]],
) -> None:
    catalog_server.clear()
    catalog_server.expect_ordered_request(
        '/books',
        query_string={'isbn': OTHER_ISBN},
    ).respond_with_data(
        status=503,
    )
    catalog_server.expect_ordered_request(
        '/books',
        query_string={'isbn': OTHER_ISBN},
    ).respond_with_json(
        {'isbn': OTHER_ISBN, 'title': 'Из каталога', 'authors': ['К'], 'year': 2001},
    )
    response = api_client.simulate_post(
        '/library/catalog_books',
        json={'isbn': OTHER_ISBN},
        headers=ADMIN,
    )
    assert response.status_code == 201
    created['books'].append(response.json['id'])
    card = api_client.simulate_get(
        '/library/book',
        params={'id': str(response.json['id'])},
    )
    assert card.json['title'] == 'Из каталога'


def test_catalog_book_not_found_is_422(
    api_client: TestClient,
    catalog_server: HTTPServer,
) -> None:
    catalog_server.clear()
    catalog_server.expect_request('/books').respond_with_data(status=404)
    response = api_client.simulate_post(
        '/library/catalog_books',
        json={'isbn': ISBN},
        headers=ADMIN,
    )
    assert response.status_code == 422
    assert response.json[0]['type'] == 'BookNotInCatalog'


@pytest.mark.parametrize(
    'path',
    ['/library/books', '/library/readers', '/library/loans'],
)
def test_list_routes_connected(api_client: TestClient, path: str) -> None:
    assert api_client.simulate_get(path).status_code == 200
