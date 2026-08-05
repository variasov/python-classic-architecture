import pytest
from falcon import testing

from demo.composite.api import create_app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / 'test.db'
    app = create_app(str(db_path))
    return testing.TestClient(app)


def test_create_cat(client):
    body = {
        'name': 'Murzik',
        'age': 3,
        'mood': 'happy',
        'movements': [
            {'timestamp': '2026-01-01T10:00:00', 'latitude': 55.75, 'longitude': 37.62},
        ],
    }
    result = client.simulate_post('/cats', json=body)
    assert result.status_code == 201
    data = result.json
    assert data['name'] == 'Murzik'
    assert data['age'] == 3
    assert data['mood'] == 'happy'
    assert len(data['movements']) == 1
    assert data['movements'][0]['latitude'] == 55.75
    assert data['id']


def test_get_cat_by_id(client):
    body = {'name': 'Barsik', 'age': 5, 'mood': 'sleepy'}
    result = client.simulate_post('/cats', json=body)
    cat_id = result.json['id']

    result = client.simulate_get(f'/cats/{cat_id}')
    assert result.status_code == 200
    data = result.json
    assert data['name'] == 'Barsik'
    assert data['age'] == 5


def test_get_cat_not_found(client):
    result = client.simulate_get('/cats/nonexistent')
    assert result.status_code == 404
    assert result.json['error'] == 'Cat not found'


def test_find_cats_by_age_range(client):
    client.simulate_post('/cats', json={'name': 'Young', 'age': 1, 'mood': 'play'})
    client.simulate_post('/cats', json={'name': 'Old', 'age': 10, 'mood': 'grumpy'})
    client.simulate_post('/cats', json={'name': 'Middle', 'age': 5, 'mood': 'ok'})

    result = client.simulate_get('/cats', params={'age_from': 3, 'age_to': 7})
    assert result.status_code == 200
    data = result.json
    assert len(data) == 1
    assert data[0]['name'] == 'Middle'

    result = client.simulate_get('/cats', params={'age_from': 1, 'age_to': 10})
    assert result.status_code == 200
    assert len(result.json) == 3

    result = client.simulate_get('/cats', params={'age_from': 0, 'age_to': 0})
    assert result.status_code == 200
    assert len(result.json) == 0


def test_create_cat_without_movements(client):
    result = client.simulate_post('/cats', json={'name': 'Pushok', 'age': 2, 'mood': 'curious'})
    assert result.status_code == 201
    assert result.json['movements'] == []


def test_create_cat_empty_name(client):
    result = client.simulate_post('/cats', json={'name': '  ', 'age': 1, 'mood': 'ok'})
    assert result.status_code == 500


def test_create_cat_empty_mood(client):
    result = client.simulate_post('/cats', json={'name': 'Cat', 'age': 1, 'mood': ''})
    assert result.status_code == 500


def test_create_cat_negative_age(client):
    result = client.simulate_post('/cats', json={'name': 'Cat', 'age': -1, 'mood': 'ok'})
    assert result.status_code == 500
