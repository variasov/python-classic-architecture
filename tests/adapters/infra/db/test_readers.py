from datetime import date

import pytest

from library.app.commands.domain.reader import (
    Contact,
    ContactEmailInvalid,
    Membership,
    Reader,
    ReaderNotFound,
)


def test_readers_repo_roundtrip(any_readers_repo, reader_factory) -> None:
    reader = reader_factory(
        membership=Membership(tier='premium', valid_until=date(2027, 5, 1)),
    )
    saved = any_readers_repo.save(reader)
    loaded = any_readers_repo.get_by_id(saved.id)
    assert loaded == saved


def test_readers_repo_update(any_readers_repo, reader_factory) -> None:
    saved = any_readers_repo.save(reader_factory())
    loaded = any_readers_repo.get_by_id(saved.id)
    loaded.full_name = 'Пётр Петров'
    loaded.contact = Contact(email='petr@example.com', phone=None)
    loaded.block()
    loaded.extend_membership(until=date(2030, 1, 1))
    any_readers_repo.save(loaded)
    actual = any_readers_repo.get_by_id(saved.id)
    assert actual.full_name == 'Пётр Петров'
    assert actual.contact.email == 'petr@example.com'
    assert actual.is_blocked
    assert actual.membership.valid_until == date(2030, 1, 1)


def test_readers_repo_not_found(any_readers_repo) -> None:
    with pytest.raises(ReaderNotFound):
        any_readers_repo.get_by_id(999999)


def test_readers_repo_invalid_is_not_saved(
    db_readers_repo,
    raw_db,
    reader_factory,
) -> None:
    before = raw_db.scalar('SELECT count(*) FROM library.readers')
    with pytest.raises(ContactEmailInvalid):
        db_readers_repo.save(reader_factory(contact=Contact(email='invalid')))
    after = raw_db.scalar('SELECT count(*) FROM library.readers')
    assert after == before


def test_readers_repo_find_membership_active(
    any_readers_repo,
    reader_factory,
) -> None:
    active = any_readers_repo.save(
        reader_factory(
            membership=Membership(
                tier='basic',
                valid_until=date(2026, 3, 10),
            ),
        ),
    )
    any_readers_repo.save(
        reader_factory(
            membership=Membership(
                tier='basic',
                valid_until=date(2026, 3, 9),
            ),
        ),
    )
    found = any_readers_repo.find(
        Reader.membership_active(on=date(2026, 3, 10)),
    )
    assert {reader.id for reader in found} == {active.id}


def test_readers_repo_find_has_tier(
    any_readers_repo,
    reader_factory,
) -> None:
    premium = any_readers_repo.save(
        reader_factory(
            membership=Membership(
                tier='premium',
                valid_until=date(2026, 3, 10),
            ),
        ),
    )
    any_readers_repo.save(reader_factory())
    found = any_readers_repo.find(Reader.has_tier(tier='premium'))
    assert {reader.id for reader in found} == {premium.id}


def test_readers_repo_find_not_blocked(
    any_readers_repo,
    reader_factory,
) -> None:
    blocked = any_readers_repo.save(reader_factory(is_blocked=True))
    active = any_readers_repo.save(reader_factory(full_name='Другой'))
    found = any_readers_repo.find(Reader.not_blocked())
    assert blocked.id not in {reader.id for reader in found}
    assert active.id in {reader.id for reader in found}


def test_readers_repo_find_combination(
    any_readers_repo,
    reader_factory,
) -> None:
    reader = any_readers_repo.save(
        reader_factory(
            membership=Membership(
                tier='premium',
                valid_until=date(2026, 3, 10),
            ),
        ),
    )
    any_readers_repo.save(
        reader_factory(
            membership=Membership(
                tier='premium',
                valid_until=date(2026, 1, 1),
            ),
        ),
    )
    criteria = (
        Reader.membership_active(on=date(2026, 3, 10))
        & Reader.has_tier(tier='premium')
    )
    found = any_readers_repo.find(criteria)
    assert {item.id for item in found} == {reader.id}
