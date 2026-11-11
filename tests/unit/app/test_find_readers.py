from collections.abc import Callable
from datetime import date
from typing import Any

import pytest

from library.app.queries.readers.find_readers import (
    FindReaders,
    FindReadersParams,
    ReaderListItemDTO,
)

FROZEN_TODAY = date(2026, 3, 10)


class FrozenDate(date):
    """Подменяет date в модуле запроса, чтобы проверить переданную дату"""

    @classmethod
    def today(cls) -> date:
        return FROZEN_TODAY


@pytest.fixture
def frozen_today(monkeypatch: pytest.MonkeyPatch) -> date:
    monkeypatch.setattr(
        'library.app.queries.readers.find_readers.date', FrozenDate
    )
    return FROZEN_TODAY


def test_returns_readers_from_gateway(
    find_readers: FindReaders,
    find_readers_gateway: Any,
    reader_list_item_factory: Callable[..., ReaderListItemDTO],
) -> None:
    readers = [
        reader_list_item_factory(id=1, full_name='Alpha'),
        reader_list_item_factory(id=2, full_name='Beta'),
    ]
    find_readers_gateway.readers = readers

    assert find_readers.run(FindReadersParams()) == readers


def test_passes_params_and_today_to_gateway(
    find_readers: FindReaders,
    find_readers_gateway: Any,
    frozen_today: date,
) -> None:
    params = FindReadersParams(limit=5, offset=10)

    find_readers.run(params)

    assert find_readers_gateway.calls == [(params, frozen_today)]


def test_params_defaults() -> None:
    params = FindReadersParams()

    assert params.limit == 20
    assert params.offset == 0


@pytest.mark.parametrize('limit', [1, 50, FindReadersParams.MAX_LIMIT])
def test_params_accept_limit_in_range(limit: int) -> None:
    assert FindReadersParams(limit=limit).limit == limit


@pytest.mark.parametrize('limit', [-1, 0, FindReadersParams.MAX_LIMIT + 1])
def test_params_reject_limit_out_of_range(limit: int) -> None:
    with pytest.raises(ValueError):
        FindReadersParams(limit=limit)


@pytest.mark.parametrize('offset', [0, 1, 1000])
def test_params_accept_non_negative_offset(offset: int) -> None:
    assert FindReadersParams(offset=offset).offset == offset


def test_params_reject_negative_offset() -> None:
    with pytest.raises(ValueError):
        FindReadersParams(offset=-1)
