def test_reader_blocks_post_parses_params(api) -> None:
    response = api.client.simulate_post(
        '/library/reader_blocks',
        json={'reader_id': 1},
    )
    assert response.status_code == 200
    params = api.block_reader.calls[0][1]
    assert params.reader_id == 1


def test_reader_blocks_post_validation(api) -> None:
    response = api.client.simulate_post(
        '/library/reader_blocks',
        json={},
    )
    assert response.status_code == 400
