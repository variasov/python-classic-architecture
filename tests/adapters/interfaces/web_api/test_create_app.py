from typing import Any, cast

from falcon import testing


def test_unknown_url_returns_404(client: testing.TestClient) -> None:
    response = client.simulate_get('/library/unknown')

    assert response.status_code == 404


def test_middleware_builds_account_for_known_user(client: testing.TestClient) -> None:
    response = client.simulate_get('/probe', headers={'X-User': 'admin'})

    assert response.status_code == 200
    assert response.json['login'] == 'admin'
    assert 'books.edit' in response.json['permissions']


def test_middleware_sets_anonymous_for_unknown_user(
    client: testing.TestClient,
) -> None:
    response = client.simulate_get('/probe', headers={'X-User': 'nobody'})

    assert response.status_code == 200
    assert response.json['login'] == 'anonymous'
    assert response.json['permissions'] == []


def test_validation_error_is_400(client: testing.TestClient) -> None:
    response = client.simulate_post('/probe', params={'kind': 'validation'})

    assert response.status_code == 400
    body: Any = response.json
    assert isinstance(body, list)
    details = cast('list[dict[str, Any]]', body)
    assert {'type', 'msg', 'ctx'} <= set(details[0])


def test_auth_error_is_403(client: testing.TestClient) -> None:
    response = client.simulate_post('/probe', params={'kind': 'auth'})

    assert response.status_code == 403
    detail = response.json[0]
    assert detail['type'] == 'PermissionDenied'
    assert detail['ctx'] == {'login': 'guest', 'permission': 'books.edit'}


def test_app_error_is_422(client: testing.TestClient) -> None:
    response = client.simulate_post('/probe', params={'kind': 'app'})

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ProbeAppError'
    assert detail['ctx'] == {'message': 'app failure'}


def test_domain_error_is_422(client: testing.TestClient) -> None:
    response = client.simulate_post('/probe', params={'kind': 'domain'})

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ProbeDomainError'
    assert detail['msg'] == 'domain failure'
