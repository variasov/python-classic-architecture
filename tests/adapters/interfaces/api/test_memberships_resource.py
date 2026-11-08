def test_memberships_put_parses_params(api) -> None:
    response = api.client.simulate_put(
        '/library/memberships',
        json={'reader_id': 1, 'until': '2030-01-01'},
    )
    assert response.status_code == 200
    params = api.extend_membership.calls[0][1]
    assert params.reader_id == 1
    assert params.until.isoformat() == '2030-01-01'


def test_memberships_put_validation(api) -> None:
    response = api.client.simulate_put(
        '/library/memberships',
        json={'reader_id': 'bad', 'until': '2030-01-01'},
    )
    assert response.status_code == 400
