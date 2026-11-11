from datetime import date
from typing import Any

from falcon import testing

from library.app.commands.domain.reader import MembershipNotExtended, ReaderNotFound
from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembershipParams,
)
from library.app.roles import PermissionDenied

BODY: dict[str, Any] = {'reader_id': 5, 'valid_until': '2027-01-31'}


def test_extend_membership_returns_200(client: testing.TestClient) -> None:
    response = client.simulate_put(
        '/library/memberships', headers={'X-User': 'admin'}, json=BODY
    )

    assert response.status_code == 200


def test_request_body_is_parsed_into_params(
    client: testing.TestClient, extend_membership_fake: Any
) -> None:
    client.simulate_put(
        '/library/memberships', headers={'X-User': 'admin'}, json=BODY
    )

    params, account = extend_membership_fake.calls[0]
    assert params == ExtendMembershipParams(
        reader_id=5, valid_until=date(2027, 1, 31)
    )
    assert account.login == 'admin'


def test_missing_field_is_400(
    client: testing.TestClient, extend_membership_fake: Any
) -> None:
    body = {key: value for key, value in BODY.items() if key != 'valid_until'}

    response = client.simulate_put(
        '/library/memberships', headers={'X-User': 'admin'}, json=body
    )

    assert response.status_code == 400
    assert extend_membership_fake.calls == []


def test_invalid_date_is_400(
    client: testing.TestClient, extend_membership_fake: Any
) -> None:
    response = client.simulate_put(
        '/library/memberships',
        headers={'X-User': 'admin'},
        json={**BODY, 'valid_until': 'not-a-date'},
    )

    assert response.status_code == 400
    assert extend_membership_fake.calls == []


def test_invalid_reader_id_is_400(
    client: testing.TestClient, extend_membership_fake: Any
) -> None:
    response = client.simulate_put(
        '/library/memberships',
        headers={'X-User': 'admin'},
        json={**BODY, 'reader_id': 'not-a-number'},
    )

    assert response.status_code == 400
    assert extend_membership_fake.calls == []


def test_not_extended_is_422(
    client: testing.TestClient, extend_membership_fake: Any
) -> None:
    extend_membership_fake.error = MembershipNotExtended(
        reader_id=5, until=date(2027, 1, 31)
    )

    response = client.simulate_put(
        '/library/memberships', headers={'X-User': 'admin'}, json=BODY
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'MembershipNotExtended'
    assert detail['ctx'] == {'reader_id': 5, 'until': '2027-01-31'}


def test_missing_reader_is_422(
    client: testing.TestClient, extend_membership_fake: Any
) -> None:
    extend_membership_fake.error = ReaderNotFound(id=5)

    response = client.simulate_put(
        '/library/memberships', headers={'X-User': 'admin'}, json=BODY
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ReaderNotFound'
    assert detail['ctx'] == {'id': 5}


def test_permission_denied_is_403(
    client: testing.TestClient, extend_membership_fake: Any
) -> None:
    extend_membership_fake.error = PermissionDenied(
        login='guest', permission='readers.edit'
    )

    response = client.simulate_put(
        '/library/memberships', headers={'X-User': 'guest'}, json=BODY
    )

    assert response.status_code == 403
