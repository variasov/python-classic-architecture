from typing import Any

from falcon import testing

from library.app.commands.books.create_book_from_catalog import (
    BookNotInCatalog,
)
from library.app.roles import PermissionDenied

ISBN = '9785171183660'


def test_create_book_returns_201_and_id(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/catalog_books',
        headers={'X-User': 'admin'},
        json={'isbn': ISBN},
    )

    assert response.status_code == 201
    assert response.json == {'id': 3}


def test_request_body_is_passed_to_use_case(
    client: testing.TestClient,
    create_catalog_book_fake: Any,
) -> None:
    client.simulate_post(
        '/library/catalog_books',
        headers={'X-User': 'admin'},
        json={'isbn': ISBN},
    )

    params, account = create_catalog_book_fake.calls[0]
    assert params == {'isbn': ISBN}
    assert account.login == 'admin'


def test_book_not_in_catalog_is_422(
    client: testing.TestClient,
    create_catalog_book_fake: Any,
) -> None:
    create_catalog_book_fake.error = BookNotInCatalog(isbn=ISBN)

    response = client.simulate_post(
        '/library/catalog_books',
        headers={'X-User': 'admin'},
        json={'isbn': ISBN},
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'BookNotInCatalog'
    assert detail['ctx'] == {'isbn': ISBN}


def test_permission_denied_is_403(
    client: testing.TestClient,
    create_catalog_book_fake: Any,
) -> None:
    create_catalog_book_fake.error = PermissionDenied(
        login='guest',
        permission='books.edit',
    )

    response = client.simulate_post(
        '/library/catalog_books',
        headers={'X-User': 'guest'},
        json={'isbn': ISBN},
    )

    assert response.status_code == 403
