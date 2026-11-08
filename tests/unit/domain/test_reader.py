from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from library.app.commands.domain.reader import (
    Contact,
    ContactEmailInvalid,
    Membership,
    MembershipTierInvalid,
    Reader,
    ReaderNameEmpty,
)


def test_valid_reader_passes_check(reader_factory) -> None:
    reader_factory().check()


@given(st.text(alphabet=' \t', min_size=1, max_size=5))
def test_whitespace_name_is_invalid(name: str) -> None:
    reader = Reader(
        full_name=name,
        contact=Contact(email='ivan@example.com'),
        membership=Membership(tier='basic', valid_until=date(2027, 1, 1)),
    )
    with pytest.raises(ReaderNameEmpty):
        reader.check()


def test_empty_name_is_invalid(reader_factory) -> None:
    with pytest.raises(ReaderNameEmpty) as exc_info:
        reader_factory(full_name='').check()
    assert str(exc_info.value) == 'ФИО читателя не может быть пустым'


@given(
    st.text(
        alphabet=st.characters(blacklist_characters='@'),
        min_size=0,
        max_size=20,
    ),
)
def test_email_without_at_is_invalid(email: str) -> None:
    with pytest.raises(ContactEmailInvalid) as exc_info:
        Contact(email=email).check()
    assert exc_info.value.email == email


def test_contact_with_at_is_valid() -> None:
    Contact(email='a@b').check()


def test_invalid_tier_is_rejected() -> None:
    with pytest.raises(MembershipTierInvalid) as exc_info:
        Membership(tier='vip', valid_until=date(2027, 1, 1)).check()
    assert exc_info.value.tier == 'vip'


def test_basic_membership_limit() -> None:
    membership = Membership(tier='basic', valid_until=date(2027, 1, 1))
    assert membership.loan_limit == 3


def test_premium_membership_limit() -> None:
    membership = Membership(tier='premium', valid_until=date(2027, 1, 1))
    assert membership.loan_limit == 10


def test_extend_membership_changes_valid_until(reader_factory) -> None:
    reader = reader_factory()
    reader.extend_membership(until=date(2030, 1, 1))
    assert reader.membership.valid_until == date(2030, 1, 1)
    assert reader.membership.tier == 'basic'


def test_block_and_unblock(reader_factory) -> None:
    reader = reader_factory()
    reader.block()
    assert reader.is_blocked is True
    reader.unblock()
    assert reader.is_blocked is False


def test_membership_active_in_both_forms(reader_factory) -> None:
    reader = reader_factory(
        membership=Membership(
            tier='basic',
            valid_until=date(2026, 3, 10),
        ),
    )
    assert reader.membership_active(on=date(2026, 3, 10))
    assert not reader.membership_active(on=date(2026, 3, 11))
    assert Reader.membership_active(on=date(2026, 3, 10)).is_satisfied_by(
        reader,
    )


def test_has_tier_in_both_forms(reader_factory) -> None:
    reader = reader_factory(
        membership=Membership(tier='premium', valid_until=date(2027, 1, 1)),
    )
    assert reader.has_tier(tier='premium')
    assert not reader.has_tier(tier='basic')
    assert Reader.has_tier(tier='premium').is_satisfied_by(reader)


def test_not_blocked_in_both_forms(reader_factory) -> None:
    reader = reader_factory()
    assert reader.not_blocked()
    assert Reader.not_blocked().is_satisfied_by(reader)
    reader.block()
    assert not reader.not_blocked()
    assert not Reader.not_blocked().is_satisfied_by(reader)


def test_reader_criteria_combinations(reader_factory) -> None:
    reader = reader_factory()
    combined = Reader.membership_active(on=date(2026, 1, 1)) & Reader.not_blocked()
    assert combined.is_satisfied_by(reader)
    either = Reader.has_tier(tier='premium') | Reader.not_blocked()
    assert either.is_satisfied_by(reader)
    assert not (
        Reader.has_tier(tier='premium') & Reader.not_blocked()
    ).is_satisfied_by(reader)


def test_membership_is_frozen() -> None:
    membership = Membership(tier='basic', valid_until=date(2027, 1, 1))
    with pytest.raises(AttributeError):
        membership.tier = 'premium'  # type: ignore[misc]


def test_reader_defaults_id_is_none(reader_factory) -> None:
    assert reader_factory().id is None


def test_reader_type_is_reader(reader_factory) -> None:
    assert isinstance(reader_factory(), Reader)
