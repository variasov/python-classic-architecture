from datetime import date
from typing import Any

import pytest
from library.app.commands.domain.reader import (
    Contact,
    FullNameEmpty,
    InvalidEmail,
    InvalidTier,
    Membership,
    MembershipNotExtended,
    Reader,
)

TODAY = date(2026, 6, 15)


def make_reader(**overrides: Any) -> Reader:
    fields: dict[str, Any] = {
        'full_name': 'Иван Иванов',
        'contact': Contact(email='i@example.com'),
        'membership': Membership(tier='basic', valid_until=TODAY),
    }
    return Reader(**{**fields, **overrides})


def test_valid_reader() -> None:
    make_reader().check()


@pytest.mark.parametrize('name', ['', '   '])
def test_blank_full_name(name: str) -> None:
    with pytest.raises(FullNameEmpty):
        make_reader(full_name=name).check()


def test_invalid_email() -> None:
    with pytest.raises(InvalidEmail):
        make_reader(contact=Contact(email='no-at')).check()


def test_invalid_tier() -> None:
    with pytest.raises(InvalidTier):
        make_reader(membership=Membership(tier='gold', valid_until=TODAY)).check()


def test_loan_limits() -> None:
    assert Membership(tier='basic', valid_until=TODAY).loan_limit == 3
    assert Membership(tier='premium', valid_until=TODAY).loan_limit == 10


def test_extend_membership_boundary() -> None:
    reader = make_reader()
    with pytest.raises(MembershipNotExtended):
        reader.extend_membership(TODAY)
    reader.extend_membership(date(2026, 6, 16))
    assert reader.membership.valid_until == date(2026, 6, 16)


def test_block_unblock() -> None:
    reader = make_reader()
    reader.block()
    assert reader.is_blocked
    reader.unblock()
    assert not reader.is_blocked


def test_criteria() -> None:
    reader = make_reader()
    assert reader.membership_active(on=TODAY)
    assert not reader.membership_active(on=date(2026, 6, 16))
    assert reader.has_tier(tier='basic')
    assert reader.not_blocked()
    reader.block()
    assert not Reader.not_blocked().is_satisfied_by(reader)
    active_and_free = Reader.membership_active(on=TODAY) & Reader.not_blocked()
    assert not active_and_free.is_satisfied_by(reader)
    assert (~Reader.not_blocked()).is_satisfied_by(reader)
    any_tier = Reader.has_tier(tier='premium') | Reader.has_tier(tier='basic')
    assert any_tier.is_satisfied_by(reader)
