import json
from datetime import date

from library.app.commands.domain.reader import ReaderNotFound
from library.app.queries.readers.find_readers import (
    FindReadersParams,
    ReaderDTO,
)


def test_readers_get_returns_list(api) -> None:
    api.find_readers.result = [
        ReaderDTO(
            id=1,
            full_name='Иван Иванов',
            email='ivan@example.com',
            phone=None,
            tier='basic',
            valid_until=date(2027, 1, 1),
            is_blocked=False,
            active_loans=1,
            overdue_loans=0,
        ),
    ]
    response = api.client.simulate_get('/library/readers')
    assert response.status_code == 200
    assert response.json[0]['full_name'] == 'Иван Иванов'
    assert response.json[0]['valid_until'] == '2027-01-01'
    assert api.find_readers.calls[0][0] == FindReadersParams()


def test_readers_post_registers(api) -> None:
    api.register_reader.result = 5
    response = api.client.simulate_post(
        '/library/readers',
        json={
            'full_name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'valid_until': '2027-01-01',
        },
    )
    assert response.status_code == 201
    assert response.json == {'id': 5}
    params = api.register_reader.calls[0][1]
    assert params.tier == 'basic'
    assert params.phone is None


def test_readers_post_validation(api) -> None:
    response = api.client.simulate_post(
        '/library/readers',
        json={'full_name': 'Иван Иванов'},
    )
    assert response.status_code == 400


def test_readers_post_domain_error(api) -> None:
    api.register_reader.error = ReaderNotFound(id=1)
    response = api.client.simulate_post(
        '/library/readers',
        json={
            'full_name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'valid_until': '2027-01-01',
        },
    )
    assert response.status_code == 422
    assert json.loads(response.text)[0]['type'] == 'ReaderNotFound'
