def test_copies_post_parses_params(api) -> None:
    response = api.client.simulate_post(
        '/library/copies',
        json={
            'book_id': 1,
            'inventory_number': 'INV-2',
            'hall': 'B',
            'rack': 2,
            'shelf': 3,
        },
    )
    assert response.status_code == 200
    params = api.add_copy.calls[0][1]
    assert params.book_id == 1
    assert params.hall == 'B'
    assert params.rack == 2
    assert params.shelf == 3


def test_copies_post_validation(api) -> None:
    response = api.client.simulate_post(
        '/library/copies',
        json={
            'book_id': 1,
            'inventory_number': 'INV-2',
            'hall': 'B',
            'rack': 'bad',
            'shelf': 3,
        },
    )
    assert response.status_code == 400
    assert api.add_copy.calls == []
