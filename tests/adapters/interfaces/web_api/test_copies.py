from typing import Any

from falcon import testing

from library.app.commands.books.add_copy import (
    InventoryNumberTaken,
)
from library.app.roles import PermissionDenied

COPY: dict[str, Any] = {
    'book_id': 1,
    'inventory_number': 'INV-001',
    'hall': 'Читальный зал',
    'rack': 2,
    'shelf': 3,
}


def test_add_copy_returns_201_and_id(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/copies',
        headers={'X-User': 'admin'},
        json=COPY,
    )

    assert response.status_code == 201
    assert response.json == {'id': 2}


def test_request_body_is_passed_to_use_case(
    client: testing.TestClient,
    create_copies_fake: Any,
) -> None:
    client.simulate_post(
        '/library/copies',
        headers={'X-User': 'admin'},
        json=COPY,
    )

    params, account = create_copies_fake.calls[0]
    assert params == COPY
    assert account.login == 'admin'


def test_inventory_number_taken_is_422(
    client: testing.TestClient,
    create_copies_fake: Any,
) -> None:
    create_copies_fake.error = InventoryNumberTaken(inventory_number='INV-001')

    response = client.simulate_post(
        '/library/copies',
        headers={'X-User': 'admin'},
        json=COPY,
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'InventoryNumberTaken'
    assert detail['ctx'] == {'inventory_number': 'INV-001'}


def test_permission_denied_is_403(
    client: testing.TestClient,
    create_copies_fake: Any,
) -> None:
    create_copies_fake.error = PermissionDenied(
        login='guest',
        permission='books.edit',
    )

    response = client.simulate_post(
        '/library/copies',
        headers={'X-User': 'guest'},
        json=COPY,
    )

    assert response.status_code == 403
