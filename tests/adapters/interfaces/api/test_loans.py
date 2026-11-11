from typing import Any

import pytest
from falcon import testing

from library.app.commands.domain.borrow_copy import (
    LoanLimitReached,
    ReaderHasOverdueLoans,
)
from library.app.commands.domain.copy import CopyNotAvailable
from library.app.commands.use_cases.loans.issue_loan import IssueLoanParams
from library.app.queries.loans.find_loans import FindLoansParams
from library.app.roles import PermissionDenied

LOAN: dict[str, Any] = {'reader_id': 1, 'copy_id': 2}


def test_find_loans_returns_200_and_list(
    client: testing.TestClient, find_loans_fake: Any
) -> None:
    response = client.simulate_get(
        '/library/loans',
        params={
            'reader_id': '4',
            'only_overdue': 'true',
            'only_active': 'true',
            'limit': '5',
            'offset': '1',
        },
    )

    assert response.status_code == 200
    assert response.json == [
        {
            'id': 7,
            'reader_id': 4,
            'copy_id': 2,
            'start': '2026-03-01',
            'due': '2026-03-15',
            'returned_at': None,
            'extensions_count': 1,
        }
    ]
    assert find_loans_fake.calls == [
        FindLoansParams(
            reader_id=4,
            only_overdue=True,
            only_active=True,
            limit=5,
            offset=1,
        )
    ]


def test_find_loans_uses_default_params(
    client: testing.TestClient, find_loans_fake: Any
) -> None:
    client.simulate_get('/library/loans')

    assert find_loans_fake.calls == [FindLoansParams()]


@pytest.mark.parametrize('limit', ['0', '-1', '101'])
def test_find_loans_invalid_limit_is_400(
    client: testing.TestClient, find_loans_fake: Any, limit: str
) -> None:
    response = client.simulate_get('/library/loans', params={'limit': limit})

    assert response.status_code == 400
    assert find_loans_fake.calls == []


def test_find_loans_negative_offset_is_400(
    client: testing.TestClient, find_loans_fake: Any
) -> None:
    response = client.simulate_get('/library/loans', params={'offset': '-1'})

    assert response.status_code == 400
    assert find_loans_fake.calls == []


def test_find_loans_non_integer_reader_is_400(
    client: testing.TestClient, find_loans_fake: Any
) -> None:
    response = client.simulate_get(
        '/library/loans', params={'reader_id': 'not-a-number'}
    )

    assert response.status_code == 400
    assert find_loans_fake.calls == []


def test_issue_loan_returns_201_and_id(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/loans', headers={'X-User': 'admin'}, json=LOAN
    )

    assert response.status_code == 201
    assert response.json == {'id': 5}


def test_request_body_is_parsed_into_params(
    client: testing.TestClient, issue_loan_fake: Any
) -> None:
    client.simulate_post(
        '/library/loans', headers={'X-User': 'admin'}, json=LOAN
    )

    params, account = issue_loan_fake.calls[0]
    assert params == IssueLoanParams(reader_id=1, copy_id=2)
    assert account.login == 'admin'


def test_missing_field_is_400(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/loans',
        headers={'X-User': 'admin'},
        json={'reader_id': 1},
    )

    assert response.status_code == 400


@pytest.mark.parametrize('field', ['reader_id', 'copy_id'])
def test_non_integer_field_is_400(
    client: testing.TestClient, field: str
) -> None:
    response = client.simulate_post(
        '/library/loans',
        headers={'X-User': 'admin'},
        json={**LOAN, field: 'not-a-number'},
    )

    assert response.status_code == 400


def test_permission_denied_is_403(
    client: testing.TestClient, issue_loan_fake: Any
) -> None:
    issue_loan_fake.error = PermissionDenied(
        login='guest', permission='loans.edit'
    )

    response = client.simulate_post(
        '/library/loans', headers={'X-User': 'guest'}, json=LOAN
    )

    assert response.status_code == 403


def test_unavailable_copy_is_422(
    client: testing.TestClient, issue_loan_fake: Any
) -> None:
    issue_loan_fake.error = CopyNotAvailable(copy_id=2)

    response = client.simulate_post(
        '/library/loans', headers={'X-User': 'admin'}, json=LOAN
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'CopyNotAvailable'
    assert detail['ctx'] == {'copy_id': 2}


def test_loan_limit_is_422(
    client: testing.TestClient, issue_loan_fake: Any
) -> None:
    issue_loan_fake.error = LoanLimitReached(reader_id=1, limit=3)

    response = client.simulate_post(
        '/library/loans', headers={'X-User': 'admin'}, json=LOAN
    )

    assert response.status_code == 422
    assert response.json[0]['type'] == 'LoanLimitReached'
    assert response.json[0]['ctx'] == {'reader_id': 1, 'limit': 3}


def test_reader_with_overdue_loans_is_422(
    client: testing.TestClient, issue_loan_fake: Any
) -> None:
    issue_loan_fake.error = ReaderHasOverdueLoans(reader_id=1)

    response = client.simulate_post(
        '/library/loans', headers={'X-User': 'admin'}, json=LOAN
    )

    assert response.status_code == 422
    assert response.json[0]['type'] == 'ReaderHasOverdueLoans'
