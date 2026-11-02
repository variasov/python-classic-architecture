from collections.abc import Callable
from datetime import timedelta

import pytest
from library.app.commands.domain.reader import (
    Contact,
    InvalidEmail,
    Membership,
    Reader,
    ReaderNotFound,
    ReadersRepo,
)
from library.infra.db.repos.readers_repo import DbReadersRepo

from tests.conftest import TODAY, RawDb


@pytest.fixture(params=['db_readers_repo', 'in_memory_readers_repo'])
def any_readers_repo(request: pytest.FixtureRequest) -> ReadersRepo:
    return request.getfixturevalue(request.param)


def make_reader(marker: str, **overrides: object) -> Reader:
    fields: dict[str, object] = {
        'full_name': f'Читатель {marker}',
        'contact': Contact(email=f'{marker}@e.com', phone=None),
        'membership': Membership(tier='premium', valid_until=TODAY),
    }
    return Reader(**{**fields, **overrides})  # type: ignore[arg-type]


def test_save_and_get(
    any_readers_repo: ReadersRepo,
    marker: str,
    raw_db: RawDb,
) -> None:
    reader = any_readers_repo.save(make_reader(marker))
    assert reader.id is not None
    try:
        assert any_readers_repo.get_by_id(reader.id) == reader
        reader.block()
        reader.extend_membership(TODAY + timedelta(days=5))
        any_readers_repo.save(reader)
        assert any_readers_repo.get_by_id(reader.id) == reader
    finally:
        raw_db.execute('DELETE FROM library.readers WHERE id = %(id)s', id=reader.id)


def test_not_found(any_readers_repo: ReadersRepo) -> None:
    with pytest.raises(ReaderNotFound):
        any_readers_repo.get_by_id(-1)


def test_save_unknown_id(db_readers_repo: DbReadersRepo, marker: str) -> None:
    with pytest.raises(ReaderNotFound):
        db_readers_repo.save(make_reader(marker, id=-7))


def test_save_invalid_writes_nothing(
    db_readers_repo: DbReadersRepo,
    raw_db: RawDb,
    marker: str,
) -> None:
    with pytest.raises(InvalidEmail):
        db_readers_repo.save(make_reader(marker, contact=Contact(email='bad')))
    count = raw_db.scalar(
        'SELECT count(*) FROM library.readers WHERE full_name = %(n)s',
        n=f'Читатель {marker}',
    )
    assert count == 0


def test_find_by_criteria_matches_domain(
    any_readers_repo: ReadersRepo,
    marker: str,
    raw_db: RawDb,
) -> None:
    readers = [
        any_readers_repo.save(make_reader(marker)),
        any_readers_repo.save(
            make_reader(
                marker,
                membership=Membership(
                    tier='basic',
                    valid_until=TODAY - timedelta(days=1),
                ),
            ),
        ),
        any_readers_repo.save(make_reader(marker, is_blocked=True)),
    ]
    ids = [r.id for r in readers]
    cases = [
        Reader.membership_active(on=TODAY),
        Reader.has_tier(tier='basic'),
        Reader.not_blocked(),
        Reader.membership_active(on=TODAY) & Reader.not_blocked(),
        Reader.has_tier(tier='basic') | ~Reader.not_blocked(),
    ]
    try:
        for criteria in cases:
            found = {r.id for r in any_readers_repo.find(criteria) if r.id in ids}
            expected = {r.id for r in readers if criteria.is_satisfied_by(r)}
            assert found == expected
    finally:
        raw_db.execute('DELETE FROM library.readers WHERE id = ANY(%(ids)s)', ids=ids)


def test_factory_roundtrip(
    db_readers_repo: DbReadersRepo,
    reader_factory: Callable[..., Reader],
) -> None:
    reader = reader_factory(tier='basic')
    assert reader.id is not None
    assert db_readers_repo.get_by_id(reader.id).contact.phone == '123'
