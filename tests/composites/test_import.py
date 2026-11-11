import importlib

import psycopg
import pytest


def test_importing_composite_does_not_open_db_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from library.composites.infra.db import engine as engine_module

    calls: list[object] = []

    def forbidden_connect(*args: object, **kwargs: object) -> None:
        calls.append(object())

    monkeypatch.setattr(psycopg, 'connect', forbidden_connect)

    importlib.reload(engine_module)

    assert calls == []
    assert 'engine' in vars(engine_module)
