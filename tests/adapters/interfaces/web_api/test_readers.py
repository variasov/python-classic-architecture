from typing import Any

from falcon import testing

from library.app.commands.domain.reader import ContactEmailInvalid
from library.app.roles import PermissionDenied

READER: dict[str, Any] = {
    'full_name': 'Иван Петров',
    'email': 'ivan@example.com',
    'phone': '+7 900 000-00-00',
    'tier': 'premium',
    'valid_until': '2027-01-31',
}


def test_find_readers_returns_200_and_list(
    client: testing.TestClient,
    find_readers_fake: Any,
) -> None:
    response = client.simulate_get(
        '/library/readers',
        params={'limit': '5', 'offset': '10'},
    )

    assert response.status_code == 200
    assert response.json == [
        {
            'id': 4,
            'full_name': 'Иван Петров',
            'email': 'ivan@example.com',
            'active_loans': 1,
            'overdue_loans': 0,
        },
    ]
    assert find_readers_fake.calls == [{'limit': '5', 'offset': '10'}]


def test_find_readers_without_params_passes_empty_mapping(
    client: testing.TestClient,
    find_readers_fake: Any,
) -> None:
    client.simulate_get('/library/readers')

    assert find_readers_fake.calls == [{}]


def test_register_reader_returns_201_and_id(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/readers',
        headers={'X-User': 'admin'},
        json=READER,
    )

    assert response.status_code == 201
    assert response.json == {'id': 4}


def test_request_body_is_passed_to_use_case(
    client: testing.TestClient,
    register_reader_fake: Any,
) -> None:
    client.simulate_post(
        '/library/readers',
        headers={'X-User': 'admin'},
        json=READER,
    )

    params, account = register_reader_fake.calls[0]
    assert params == READER
    assert account.login == 'admin'


def test_domain_error_is_422(
    client: testing.TestClient,
    register_reader_fake: Any,
) -> None:
    register_reader_fake.error = ContactEmailInvalid(email='ivan.example.com')

    response = client.simulate_post(
        '/library/readers',
        headers={'X-User': 'admin'},
        json=READER,
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ContactEmailInvalid'
    assert detail['ctx'] == {'email': 'ivan.example.com'}


def test_permission_denied_is_403(
    client: testing.TestClient,
    register_reader_fake: Any,
) -> None:
    register_reader_fake.error = PermissionDenied(
        login='guest',
        permission='readers.edit',
    )

    response = client.simulate_post(
        '/library/readers',
        headers={'X-User': 'guest'},
        json=READER,
    )

    assert response.status_code == 403
