from collections.abc import Callable
from datetime import date
from typing import Any

import pytest

from library.app.queries.loans.find_loans import (
    FindLoans,
    FindLoansParams,
    LoanListItemDTO,
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
        'library.app.queries.loans.find_loans.date', FrozenDate
    )
    return FROZEN_TODAY


def test_returns_loans_from_gateway(
    find_loans: FindLoans,
    find_loans_gateway: Any,
    loan_list_item_factory: Callable[..., LoanListItemDTO],
) -> None:
    loans = [
        loan_list_item_factory(id=1),
        loan_list_item_factory(id=2),
    ]
    find_loans_gateway.loans = loans

    assert find_loans.run(FindLoansParams()) == loans


def test_passes_params_and_today_to_gateway(
    find_loans: FindLoans,
    find_loans_gateway: Any,
    frozen_today: date,
) -> None:
    params = FindLoansParams(
        reader_id=7,
        only_overdue=True,
        only_active=True,
        limit=50,
        offset=5,
    )

    find_loans.run(params)

    assert find_loans_gateway.calls == [(params, frozen_today)]


def test_params_defaults() -> None:
    params = FindLoansParams()

    assert params.reader_id is None
    assert params.only_overdue is False
    assert params.only_active is False
    assert params.limit == 20
    assert params.offset == 0


@pytest.mark.parametrize('limit', [1, 50, FindLoansParams.MAX_LIMIT])
def test_params_accept_limit_in_range(limit: int) -> None:
    assert FindLoansParams(limit=limit).limit == limit


@pytest.mark.parametrize('limit', [-1, 0, FindLoansParams.MAX_LIMIT + 1])
def test_params_reject_limit_out_of_range(limit: int) -> None:
    with pytest.raises(ValueError):
        FindLoansParams(limit=limit)


@pytest.mark.parametrize('offset', [0, 1, 1000])
def test_params_accept_non_negative_offset(offset: int) -> None:
    assert FindLoansParams(offset=offset).offset == offset


def test_params_reject_negative_offset() -> None:
    with pytest.raises(ValueError):
        FindLoansParams(offset=-1)
