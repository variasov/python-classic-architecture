from collections.abc import Callable

import pytest
from classic.criteria import Criteria
from hypothesis import given
from hypothesis import strategies as st

from library.app.commands.domain.copy import (
    Copy,
    CopyNotAvailable,
    CopyNotFound,
    CopyNotTaken,
    InventoryNumberEmpty,
    ShelfLocation,
    ShelfLocationInvalid,
)


def test_valid_copy_passes_check(copy_factory: Callable[..., Copy]) -> None:
    copy_factory().check()


def test_inventory_number_cannot_be_empty(
    copy_factory: Callable[..., Copy],
) -> None:
    with pytest.raises(InventoryNumberEmpty):
        copy_factory(inventory_number='  ').check()


def test_shelf_location_must_be_positive() -> None:
    with pytest.raises(ShelfLocationInvalid):
        ShelfLocation(hall='Зал', rack=0, shelf=1).check()
    with pytest.raises(ShelfLocationInvalid):
        ShelfLocation(hall='Зал', rack=1, shelf=0).check()


@given(st.integers(max_value=0))
def test_any_non_positive_rack_is_invalid(rack: int) -> None:
    with pytest.raises(ShelfLocationInvalid):
        ShelfLocation(hall='Зал', rack=rack, shelf=1).check()


@given(st.integers(max_value=0))
def test_any_non_positive_shelf_is_invalid(shelf: int) -> None:
    with pytest.raises(ShelfLocationInvalid):
        ShelfLocation(hall='Зал', rack=1, shelf=shelf).check()


@given(st.text(max_size=20))
def test_blank_inventory_number_is_rejected(value: str) -> None:
    copy = Copy(
        book_id=1,
        inventory_number=value,
        shelf=ShelfLocation(hall='Зал', rack=1, shelf=1),
    )
    if value.strip():
        copy.check()
    else:
        with pytest.raises(InventoryNumberEmpty):
            copy.check()


def test_take_and_give_back(copy_factory: Callable[..., Copy]) -> None:
    copy = copy_factory()

    copy.take()
    assert copy.is_available is False
    copy.give_back()
    assert copy.is_available is True


def test_take_taken_copy_fails(copy_factory: Callable[..., Copy]) -> None:
    copy = copy_factory(is_available=False)

    with pytest.raises(CopyNotAvailable):
        copy.take()


def test_give_back_available_copy_fails(copy_factory: Callable[..., Copy]) -> None:
    with pytest.raises(CopyNotTaken):
        copy_factory().give_back()


def test_criteria_on_instance(copy_factory: Callable[..., Copy]) -> None:
    copy = copy_factory(book_id=5, inventory_number='INV-9', is_available=True)

    assert copy.available() is True
    assert copy.of_book(5) is True
    assert copy.of_book(6) is False
    assert copy.with_inventory_number('INV-9') is True
    assert copy.with_inventory_number('INV-0') is False


def test_criteria_lazy_form(copy_factory: Callable[..., Copy]) -> None:
    copy = copy_factory(book_id=5, inventory_number='INV-9', is_available=True)

    assert Copy.available().is_satisfied_by(copy) is True
    assert Copy.of_book(book_id=5).is_satisfied_by(copy) is True
    assert (
        Copy.with_inventory_number(inventory_number='INV-9').is_satisfied_by(copy)
        is True
    )
    assert (Copy.available() & Copy.of_book(book_id=5)).is_satisfied_by(copy) is True


def test_criteria_combinations(copy_factory: Callable[..., Copy]) -> None:
    copy = copy_factory(book_id=5, inventory_number='INV-9', is_available=True)
    available_and_of_book = Copy.available() & Copy.of_book(book_id=5)
    available_or_other_book = Copy.available() | Copy.of_book(book_id=6)
    not_of_book = ~Copy.of_book(book_id=5)

    assert isinstance(available_and_of_book, Criteria)
    assert available_and_of_book.is_satisfied_by(copy) is True
    assert available_or_other_book.is_satisfied_by(copy) is True
    assert not_of_book.is_satisfied_by(copy) is False


def test_copy_not_found_message_uses_id() -> None:
    error = CopyNotFound(id=7)

    assert '7' in str(error)
