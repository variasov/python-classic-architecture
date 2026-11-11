from typing import Any

from falcon import testing

from library.app.commands.domain.reader import (
    ReaderAlreadyBlocked,
    ReaderNotBlocked,
    ReaderNotFound,
)
from library.app.commands.use_cases.readers.block_reader import BlockReaderParams
from library.app.commands.use_cases.readers.unblock_reader import (
    UnblockReaderParams,
)
from library.app.roles import PermissionDenied


def test_block_reader_returns_200(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        json={'reader_id': 5},
    )

    assert response.status_code == 200


def test_block_request_body_is_parsed_into_params(
    client: testing.TestClient,
    block_reader_fake: Any,
) -> None:
    client.simulate_post(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        json={'reader_id': 5},
    )

    params, account = block_reader_fake.calls[0]
    assert params == BlockReaderParams(reader_id=5)
    assert account.login == 'admin'


def test_block_missing_field_is_400(
    client: testing.TestClient,
    block_reader_fake: Any,
) -> None:
    response = client.simulate_post(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        json={},
    )

    assert response.status_code == 400
    assert block_reader_fake.calls == []


def test_block_invalid_reader_id_is_400(
    client: testing.TestClient,
    block_reader_fake: Any,
) -> None:
    response = client.simulate_post(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        json={'reader_id': 'not-a-number'},
    )

    assert response.status_code == 400
    assert block_reader_fake.calls == []


def test_already_blocked_is_422(
    client: testing.TestClient,
    block_reader_fake: Any,
) -> None:
    block_reader_fake.error = ReaderAlreadyBlocked(reader_id=5)

    response = client.simulate_post(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        json={'reader_id': 5},
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ReaderAlreadyBlocked'
    assert detail['ctx'] == {'reader_id': 5}


def test_block_missing_reader_is_422(
    client: testing.TestClient,
    block_reader_fake: Any,
) -> None:
    block_reader_fake.error = ReaderNotFound(id=5)

    response = client.simulate_post(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        json={'reader_id': 5},
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ReaderNotFound'
    assert detail['ctx'] == {'id': 5}


def test_block_permission_denied_is_403(
    client: testing.TestClient,
    block_reader_fake: Any,
) -> None:
    block_reader_fake.error = PermissionDenied(
        login='guest',
        permission='readers.edit',
    )

    response = client.simulate_post(
        '/library/reader_blocks',
        headers={'X-User': 'guest'},
        json={'reader_id': 5},
    )

    assert response.status_code == 403


def test_unblock_reader_returns_200(client: testing.TestClient) -> None:
    response = client.simulate_delete(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        params={'reader_id': '5'},
    )

    assert response.status_code == 200


def test_unblock_query_is_parsed_into_params(
    client: testing.TestClient,
    unblock_reader_fake: Any,
) -> None:
    client.simulate_delete(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        params={'reader_id': '5'},
    )

    params, account = unblock_reader_fake.calls[0]
    assert params == UnblockReaderParams(reader_id=5)
    assert account.login == 'admin'


def test_unblock_without_query_is_400(
    client: testing.TestClient,
    unblock_reader_fake: Any,
) -> None:
    response = client.simulate_delete(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
    )

    assert response.status_code == 400
    assert unblock_reader_fake.calls == []


def test_unblock_invalid_query_is_400(
    client: testing.TestClient,
    unblock_reader_fake: Any,
) -> None:
    response = client.simulate_delete(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        params={'reader_id': 'not-a-number'},
    )

    assert response.status_code == 400
    assert unblock_reader_fake.calls == []


def test_unblock_not_blocked_is_422(
    client: testing.TestClient,
    unblock_reader_fake: Any,
) -> None:
    unblock_reader_fake.error = ReaderNotBlocked(reader_id=5)

    response = client.simulate_delete(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        params={'reader_id': '5'},
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ReaderNotBlocked'
    assert detail['ctx'] == {'reader_id': 5}


def test_unblock_missing_reader_is_422(
    client: testing.TestClient,
    unblock_reader_fake: Any,
) -> None:
    unblock_reader_fake.error = ReaderNotFound(id=5)

    response = client.simulate_delete(
        '/library/reader_blocks',
        headers={'X-User': 'admin'},
        params={'reader_id': '5'},
    )

    assert response.status_code == 422
    detail = response.json[0]
    assert detail['type'] == 'ReaderNotFound'
    assert detail['ctx'] == {'id': 5}


def test_unblock_permission_denied_is_403(
    client: testing.TestClient,
    unblock_reader_fake: Any,
) -> None:
    unblock_reader_fake.error = PermissionDenied(
        login='guest',
        permission='readers.edit',
    )

    response = client.simulate_delete(
        '/library/reader_blocks',
        headers={'X-User': 'guest'},
        params={'reader_id': '5'},
    )

    assert response.status_code == 403
