from typing import Any

from falcon import testing

from library.app.commands.domain.loan import LoanAlreadyReturned, LoanNotFound
from library.app.roles import PermissionDenied

BODY: dict[str, Any] = {'loan_id': 5}


def test_return_loan_returns_200(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/returns',
        headers={'X-User': 'admin'},
        json=BODY,
    )

    assert response.status_code == 200


def test_request_body_is_passed_to_use_case(
    client: testing.TestClient,
    return_loan_fake: Any,
) -> None:
    client.simulate_post(
        '/library/returns',
        headers={'X-User': 'admin'},
        json=BODY,
    )

    params, account = return_loan_fake.calls[0]
    assert params == BODY
    assert account.login == 'admin'


def test_permission_denied_is_403(
    client: testing.TestClient,
    return_loan_fake: Any,
) -> None:
    return_loan_fake.error = PermissionDenied(
        login='guest',
        permission='loans.edit',
    )

    response = client.simulate_post(
        '/library/returns',
        headers={'X-User': 'guest'},
        json=BODY,
    )

    assert response.status_code == 403


def test_missing_loan_is_422(
    client: testing.TestClient,
    return_loan_fake: Any,
) -> None:
    return_loan_fake.error = LoanNotFound(id=5)

    response = client.simulate_post(
        '/library/returns',
        headers={'X-User': 'admin'},
        json=BODY,
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'LoanNotFound'
    assert detail['ctx'] == {'id': 5}


def test_already_returned_is_422(
    client: testing.TestClient,
    return_loan_fake: Any,
) -> None:
    return_loan_fake.error = LoanAlreadyReturned(loan_id=5)

    response = client.simulate_post(
        '/library/returns',
        headers={'X-User': 'admin'},
        json=BODY,
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'LoanAlreadyReturned'
    assert detail['ctx'] == {'loan_id': 5}
