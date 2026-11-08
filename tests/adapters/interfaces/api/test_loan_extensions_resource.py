def test_loan_extensions_post_parses_params(api) -> None:
    response = api.client.simulate_post(
        '/library/loan_extensions',
        json={'loan_id': 1, 'days': 7},
    )
    assert response.status_code == 200
    params = api.extend_loan.calls[0][1]
    assert params.loan_id == 1
    assert params.days == 7


def test_loan_extensions_post_validation(api) -> None:
    response = api.client.simulate_post(
        '/library/loan_extensions',
        json={'loan_id': 1, 'days': 'bad'},
    )
    assert response.status_code == 400
