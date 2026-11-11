from datetime import date
from typing import Any

import pytest
from falcon import testing

from library.app.commands.domain.reader import ContactEmailInvalid
from library.app.commands.use_cases.readers.register_reader import (
    RegisterReaderParams,
)
from library.app.queries.readers.find_readers import FindReadersParams
from library.app.roles import PermissionDenied

READER: dict[str, Any] = {
    'full_name': 'Иван Петров',
    'email': 'ivan@example.com',
    'phone': '+7 900 000-00-00',
    'tier': 'premium',
    'valid_until': '2027-01-31',
}


@pytest.mark.parametrize('limit', ['0', '-1', '101'])
def test_find_readers_invalid_limit_is_400(
    client: testing.TestClient, find_readers_fake: Any, limit: str
) -> None:
    response = client.simulate_get(
        '/library/readers', params={'limit': limit}
    )

    assert response.status_code == 400
    assert find_readers_fake.calls == []


def test_find_readers_negative_offset_is_400(
    client: testing.TestClient, find_readers_fake: Any
) -> None:
    response = client.simulate_get(
        '/library/readers', params={'offset': '-1'}
    )

    assert response.status_code == 400
    assert find_readers_fake.calls == []


def test_find_readers_returns_200_and_list(
    client: testing.TestClient, find_readers_fake: Any
) -> None:
    response = client.simulate_get(
        '/library/readers', params={'limit': '5', 'offset': '10'}
    )

    assert response.status_code == 200
    assert response.json == [
        {
            'id': 4,
            'full_name': 'Иван Петров',
            'email': 'ivan@example.com',
            'active_loans': 1,
            'overdue_loans': 0,
        }
    ]
    assert find_readers_fake.calls == [
        FindReadersParams(limit=5, offset=10)
    ]


def test_find_readers_uses_default_params(
    client: testing.TestClient, find_readers_fake: Any
) -> None:
    client.simulate_get('/library/readers')

    assert find_readers_fake.calls == [FindReadersParams()]


def test_register_reader_returns_201_and_id(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/readers', headers={'X-User': 'admin'}, json=READER
    )

    assert response.status_code == 201
    assert response.json == {'id': 4}


def test_request_body_is_parsed_into_params(
    client: testing.TestClient, register_reader_fake: Any
) -> None:
    client.simulate_post(
        '/library/readers', headers={'X-User': 'admin'}, json=READER
    )

    params, account = register_reader_fake.calls[0]
    assert params == RegisterReaderParams(
        full_name='Иван Петров',
        email='ivan@example.com',
        phone='+7 900 000-00-00',
        tier='premium',
        valid_until=date(2027, 1, 31),
    )
    assert account.login == 'admin'


def test_null_phone_is_accepted(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/readers',
        headers={'X-User': 'admin'},
        json={**READER, 'phone': None},
    )

    assert response.status_code == 201


def test_missing_field_is_400(client: testing.TestClient) -> None:
    body = {key: value for key, value in READER.items() if key != 'email'}

    response = client.simulate_post(
        '/library/readers', headers={'X-User': 'admin'}, json=body
    )

    assert response.status_code == 400


def test_invalid_date_is_400(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/readers',
        headers={'X-User': 'admin'},
        json={**READER, 'valid_until': 'not-a-date'},
    )

    assert response.status_code == 400


def test_domain_error_is_422(
    client: testing.TestClient, register_reader_fake: Any
) -> None:
    register_reader_fake.error = ContactEmailInvalid(email='ivan.example.com')

    response = client.simulate_post(
        '/library/readers', headers={'X-User': 'admin'}, json=READER
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ContactEmailInvalid'
    assert detail['ctx'] == {'email': 'ivan.example.com'}


def test_permission_denied_is_403(
    client: testing.TestClient, register_reader_fake: Any
) -> None:
    register_reader_fake.error = PermissionDenied(
        login='guest', permission='readers.edit'
    )

    response = client.simulate_post(
        '/library/readers', headers={'X-User': 'guest'}, json=READER
    )

    assert response.status_code == 403
