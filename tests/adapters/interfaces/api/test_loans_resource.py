from datetime import date

from library.app.queries.loans.find_loans import LoanDTO


def test_loans_get_returns_list(api) -> None:
    api.find_loans.result = [
        LoanDTO(
            id=1,
            reader_id=1,
            book_id=1,
            inventory_number='INV-1',
            issued_at=date(2026, 3, 1),
            due=date(2026, 3, 15),
            returned_at=None,
            extensions_count=0,
        ),
    ]
    response = api.client.simulate_get(
        '/library/loans',
        params={'reader_id': '1', 'only_active': 'true'},
    )
    assert response.status_code == 200
    assert response.json[0]['id'] == 1
    params = api.find_loans.calls[0][0]
    assert params.reader_id == 1
    assert params.only_active is True


def test_loans_post_issues_loan(api) -> None:
    api.issue_loan.result = 9
    response = api.client.simulate_post(
        '/library/loans',
        json={
            'reader_id': 1,
            'book_id': 2,
            'inventory_number': 'INV-1',
        },
    )
    assert response.status_code == 201
    assert response.json == {'id': 9}


def test_loans_post_validation(api) -> None:
    response = api.client.simulate_post(
        '/library/loans',
        json={'reader_id': 1},
    )
    assert response.status_code == 400
