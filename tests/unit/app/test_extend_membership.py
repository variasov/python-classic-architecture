import logging
from collections.abc import Callable
from datetime import date

import pytest
from classic.criteria import ReturnsTrue

from library.app.commands.domain.reader import (
    Membership,
    MembershipNotExtended,
    Reader,
    ReaderNotFound,
    ReadersRepo,
)
from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
    ExtendMembershipParams,
)
from library.app.roles import Account, PermissionDenied, Permissions

VALID_UNTIL = date(2027, 1, 31)
NEW_VALID_UNTIL = date(2028, 1, 31)


@pytest.fixture
def readers_repo(in_memory_readers_repo: ReadersRepo) -> ReadersRepo:
    return in_memory_readers_repo


@pytest.fixture
def extend_membership(readers_repo: ReadersRepo) -> ExtendMembership:
    return ExtendMembership(readers=readers_repo, logger=logging.getLogger('test'))


@pytest.fixture
def extend_membership_params() -> Callable[..., ExtendMembershipParams]:
    def factory(**overrides: object) -> ExtendMembershipParams:
        fields: dict[str, object] = {
            'reader_id': 1,
            'valid_until': NEW_VALID_UNTIL,
        }
        fields.update(overrides)
        return ExtendMembershipParams(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def no_readers_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.BOOKS_EDIT,))


@pytest.fixture
def saved_reader(
    readers_repo: ReadersRepo,
    reader_factory: Callable[..., Reader],
) -> Reader:
    return readers_repo.save(
        reader_factory(
            membership=Membership(tier='premium', valid_until=VALID_UNTIL),
        ),
    )


def _load(repo: ReadersRepo, reader: Reader) -> Reader:
    assert reader.id is not None
    return repo.get_by_id(reader.id)


def test_extends_membership(
    extend_membership: ExtendMembership,
    readers_repo: ReadersRepo,
    saved_reader: Reader,
    admin: Account,
    extend_membership_params: Callable[..., ExtendMembershipParams],
) -> None:
    params = extend_membership_params(
        reader_id=saved_reader.id,
        valid_until=NEW_VALID_UNTIL,
    )

    extend_membership.run(params, admin)

    saved = _load(readers_repo, saved_reader)
    assert saved.membership == Membership(
        tier='premium',
        valid_until=NEW_VALID_UNTIL,
    )
    assert saved.is_blocked is False


def test_missing_reader_raises(
    extend_membership: ExtendMembership,
    readers_repo: ReadersRepo,
    admin: Account,
    extend_membership_params: Callable[..., ExtendMembershipParams],
) -> None:
    params = extend_membership_params(reader_id=987654)

    with pytest.raises(ReaderNotFound):
        extend_membership.run(params, admin)

    assert readers_repo.find(ReturnsTrue()) == []


def test_same_date_is_rejected(
    extend_membership: ExtendMembership,
    readers_repo: ReadersRepo,
    saved_reader: Reader,
    admin: Account,
    extend_membership_params: Callable[..., ExtendMembershipParams],
) -> None:
    params = extend_membership_params(
        reader_id=saved_reader.id,
        valid_until=VALID_UNTIL,
    )

    with pytest.raises(MembershipNotExtended):
        extend_membership.run(params, admin)

    saved = _load(readers_repo, saved_reader)
    assert saved.membership.valid_until == VALID_UNTIL


def test_earlier_date_is_rejected(
    extend_membership: ExtendMembership,
    readers_repo: ReadersRepo,
    saved_reader: Reader,
    admin: Account,
    extend_membership_params: Callable[..., ExtendMembershipParams],
) -> None:
    params = extend_membership_params(
        reader_id=saved_reader.id,
        valid_until=date(2026, 1, 1),
    )

    with pytest.raises(MembershipNotExtended):
        extend_membership.run(params, admin)

    saved = _load(readers_repo, saved_reader)
    assert saved.membership.valid_until == VALID_UNTIL


def test_requires_permission_before_storage(
    extend_membership: ExtendMembership,
    readers_repo: ReadersRepo,
    saved_reader: Reader,
    no_readers_permission: Account,
    extend_membership_params: Callable[..., ExtendMembershipParams],
) -> None:
    params = extend_membership_params(
        reader_id=987654,
        valid_until=NEW_VALID_UNTIL,
    )

    with pytest.raises(PermissionDenied):
        extend_membership.run(params, no_readers_permission)

    saved = _load(readers_repo, saved_reader)
    assert saved.membership.valid_until == VALID_UNTIL
