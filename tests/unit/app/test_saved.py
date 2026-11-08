import pytest

from library.app.commands.saved import EntityNotSaved, saved_id


def test_saved_id_returns_value() -> None:
    assert saved_id(7) == 7


def test_saved_id_requires_saved_entity() -> None:
    with pytest.raises(EntityNotSaved) as exc_info:
        saved_id(None)
    assert str(exc_info.value) == (
        'Сущность должна быть сохранена перед получением id'
    )
