from typing import Any

import pytest
from falcon import testing

from library.app.commands.domain.loan import (
    LoanAlreadyReturned,
    LoanNotFound,
    LoanOverdue,
)
from library.app.commands.use_cases.loans.extend_loan import ExtendLoanParams
from library.app.roles import PermissionDenied

BODY: dict[str, Any] = {'loan_id': 5, 'days': 7}


def test_extend_loan_returns_200(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/loan_extensions', headers={'X-User': 'admin'}, json=BODY
    )

    assert response.status_code == 200


def test_request_body_is_parsed_into_params(
    client: testing.TestClient, extend_loan_fake: Any
) -> None:
    client.simulate_post(
        '/library/loan_extensions', headers={'X-User': 'admin'}, json=BODY
    )

    params, account = extend_loan_fake.calls[0]
    assert params == ExtendLoanParams(loan_id=5, days=7)
    assert account.login == 'admin'


def test_missing_field_is_400(
    client: testing.TestClient, extend_loan_fake: Any
) -> None:
    response = client.simulate_post(
        '/library/loan_extensions',
        headers={'X-User': 'admin'},
        json={'loan_id': 5},
    )

    assert response.status_code == 400
    assert extend_loan_fake.calls == []


@pytest.mark.parametrize('days', [0, 31])
def test_days_out_of_range_are_400(
    client: testing.TestClient, extend_loan_fake: Any, days: int
) -> None:
    response = client.simulate_post(
        '/library/loan_extensions',
        headers={'X-User': 'admin'},
        json={**BODY, 'days': days},
    )

    assert response.status_code == 400
    assert extend_loan_fake.calls == []


def test_non_integer_days_are_400(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/loan_extensions',
        headers={'X-User': 'admin'},
        json={**BODY, 'days': 'not-a-number'},
    )

    assert response.status_code == 400


def test_permission_denied_is_403(
    client: testing.TestClient, extend_loan_fake: Any
) -> None:
    extend_loan_fake.error = PermissionDenied(
        login='guest', permission='loans.edit'
    )

    response = client.simulate_post(
        '/library/loan_extensions', headers={'X-User': 'guest'}, json=BODY
    )

    assert response.status_code == 403


def test_missing_loan_is_422(
    client: testing.TestClient, extend_loan_fake: Any
) -> None:
    extend_loan_fake.error = LoanNotFound(id=5)

    response = client.simulate_post(
        '/library/loan_extensions', headers={'X-User': 'admin'}, json=BODY
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'LoanNotFound'
    assert detail['ctx'] == {'id': 5}


def test_returned_loan_is_422(
    client: testing.TestClient, extend_loan_fake: Any
) -> None:
    extend_loan_fake.error = LoanAlreadyReturned(loan_id=5)

    response = client.simulate_post(
        '/library/loan_extensions', headers={'X-User': 'admin'}, json=BODY
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'LoanAlreadyReturned'
    assert detail['ctx'] == {'loan_id': 5}


def test_overdue_loan_is_422(
    client: testing.TestClient, extend_loan_fake: Any
) -> None:
    extend_loan_fake.error = LoanOverdue(loan_id=5)

    response = client.simulate_post(
        '/library/loan_extensions', headers={'X-User': 'admin'}, json=BODY
    )

    assert response.status_code == 422
    assert response.json[0]['type'] == 'LoanOverdue'
