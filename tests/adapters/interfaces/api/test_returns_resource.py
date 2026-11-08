def test_returns_post_parses_params(api) -> None:
    response = api.client.simulate_post(
        '/library/returns',
        json={'loan_id': 1},
    )
    assert response.status_code == 200
    params = api.return_loan.calls[0][1]
    assert params.loan_id == 1


def test_returns_post_validation(api) -> None:
    response = api.client.simulate_post(
        '/library/returns',
        json={},
    )
    assert response.status_code == 400
