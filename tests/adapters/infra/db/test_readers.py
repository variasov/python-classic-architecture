from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from classic.criteria import Criteria, ReturnsTrue

from library.app.commands.domain.reader import (
    Contact,
    ContactEmailInvalid,
    Membership,
    Reader,
    ReaderNotFound,
    ReadersRepo,
)
from library.infra.db.repos.readers import DbReadersRepo

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)


@pytest.fixture(params=['db', 'in_memory'])
def readers_env(request: pytest.FixtureRequest, db_engine: Any) -> ReadersRepo:
    """Репозиторий читателей: настоящий и in-memory"""
    if request.param == 'db':
        return DbReadersRepo(db_engine)
    repo: ReadersRepo = request.getfixturevalue('in_memory_readers_repo')
    return repo


@pytest.fixture
def seeded_readers(
    readers_env: ReadersRepo, reader_factory: Callable[..., Reader]
) -> list[Reader]:
    return [
        readers_env.save(
            reader_factory(
                full_name='Активный базовый',
                contact=Contact(email='active-basic@example.com'),
                membership=Membership(tier='basic', valid_until=TODAY),
            )
        ),
        readers_env.save(
            reader_factory(
                full_name='Просроченный базовый',
                contact=Contact(email='expired-basic@example.com'),
                membership=Membership(tier='basic', valid_until=YESTERDAY),
            )
        ),
        readers_env.save(
            reader_factory(
                full_name='Активный премиум',
                contact=Contact(email='active-premium@example.com'),
                membership=Membership(tier='premium', valid_until=TOMORROW),
            )
        ),
        readers_env.save(
            reader_factory(
                full_name='Заблокированный премиум',
                contact=Contact(email='blocked-premium@example.com'),
                membership=Membership(tier='premium', valid_until=TOMORROW),
                is_blocked=True,
            )
        ),
    ]


def _load(repo: ReadersRepo, reader: Reader) -> Reader:
    assert reader.id is not None
    return repo.get_by_id(reader.id)


@pytest.mark.parametrize('phone', [None, '+7 900 000-00-00'])
def test_saved_reader_is_read_back(
    readers_env: ReadersRepo,
    reader_factory: Callable[..., Reader],
    phone: str | None,
) -> None:
    reader = readers_env.save(
        reader_factory(contact=Contact(email='reader@example.com', phone=phone))
    )

    loaded = _load(readers_env, reader)

    assert loaded == reader
    assert loaded.contact.phone == phone


def test_update_changes_reader_fields(
    readers_env: ReadersRepo, reader_factory: Callable[..., Reader]
) -> None:
    reader = readers_env.save(reader_factory())
    reader.full_name = 'Пётр Сидоров'
    reader.contact = Contact(email='petr@example.com', phone='123')
    reader.membership = Membership(tier='premium', valid_until=TOMORROW)
    reader.is_blocked = True
    readers_env.save(reader)

    loaded = _load(readers_env, reader)

    assert loaded == reader


def test_get_missing_reader_raises(readers_env: ReadersRepo) -> None:
    with pytest.raises(ReaderNotFound):
        readers_env.get_by_id(987654)


def test_save_invalid_reader_writes_nothing(
    readers_env: ReadersRepo, reader_factory: Callable[..., Reader]
) -> None:
    with pytest.raises(ContactEmailInvalid):
        readers_env.save(
            reader_factory(contact=Contact(email='reader.example.com'))
        )

    assert readers_env.find(ReturnsTrue()) == []


def _criteria_map() -> dict[str, Criteria[Reader]]:
    return {
        'membership_active': Reader.membership_active(on=TODAY),
        'basic': Reader.has_tier(tier='basic'),
        'premium': Reader.has_tier(tier='premium'),
        'not_blocked': Reader.not_blocked(),
        'active_and_premium': Reader.membership_active(on=TODAY)
        & Reader.has_tier(tier='premium'),
        'active_or_premium': Reader.membership_active(on=TODAY)
        | Reader.has_tier(tier='premium'),
        'not_blocked_and_basic': Reader.not_blocked()
        & Reader.has_tier(tier='basic'),
        'expired': ~Reader.membership_active(on=TODAY),
    }


@pytest.mark.parametrize(
    'criteria_name',
    [
        'membership_active',
        'basic',
        'premium',
        'not_blocked',
        'active_and_premium',
        'active_or_premium',
        'not_blocked_and_basic',
        'expired',
    ],
)
def test_criteria_sql_matches_domain(
    readers_env: ReadersRepo,
    seeded_readers: list[Reader],
    criteria_name: str,
) -> None:
    criteria = _criteria_map()[criteria_name]

    found = readers_env.find(criteria)
    expected = [
        reader for reader in seeded_readers if criteria.is_satisfied_by(reader)
    ]

    assert [reader.id for reader in found] == [reader.id for reader in expected]


def test_find_returns_all_without_filters(
    readers_env: ReadersRepo, seeded_readers: list[Reader]
) -> None:
    assert len(readers_env.find(ReturnsTrue())) == len(seeded_readers)
