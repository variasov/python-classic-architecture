from collections.abc import Callable
from datetime import date, timedelta

import pytest
from classic.criteria import Criteria
from hypothesis import given, strategies as st

from library.app.commands.domain.reader import (
    Contact,
    ContactEmailInvalid,
    Membership,
    MembershipTierInvalid,
    Reader,
    ReaderNameEmpty,
    ReaderNotFound,
)

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)


def _reader(
    reader_factory: Callable[..., Reader],
    *,
    tier: str = 'basic',
    valid_until: date = TOMORROW,
    is_blocked: bool = False,
) -> Reader:
    return reader_factory(
        membership=Membership(tier=tier, valid_until=valid_until),
        is_blocked=is_blocked,
    )


def test_valid_reader_passes_check(
    reader_factory: Callable[..., Reader],
) -> None:
    reader_factory().check()


def test_full_name_cannot_be_empty(
    reader_factory: Callable[..., Reader],
) -> None:
    with pytest.raises(ReaderNameEmpty):
        reader_factory(full_name='').check()
    with pytest.raises(ReaderNameEmpty):
        reader_factory(full_name='   ').check()


@given(st.text(max_size=20))
def test_blank_full_name_is_rejected(value: str) -> None:
    reader = Reader(
        full_name=value,
        contact=Contact(email='reader@example.com'),
        membership=Membership(tier='basic', valid_until=TOMORROW),
    )
    if value.strip():
        reader.check()
    else:
        with pytest.raises(ReaderNameEmpty):
            reader.check()


def test_email_must_contain_at() -> None:
    with pytest.raises(ContactEmailInvalid):
        Contact(email='reader.example.com').check()
    with pytest.raises(ContactEmailInvalid):
        Contact(email='').check()

    Contact(email='reader@example.com').check()


@given(st.text(alphabet=st.characters(blacklist_characters='@'), max_size=30))
def test_any_email_without_at_is_rejected(value: str) -> None:
    with pytest.raises(ContactEmailInvalid):
        Contact(email=value).check()


@given(st.emails())
def test_any_email_with_at_is_accepted(value: str) -> None:
    Contact(email=value).check()


def test_phone_is_optional(reader_factory: Callable[..., Reader]) -> None:
    assert reader_factory().contact.phone is None
    assert contact_with_phone().phone == '+7 900 000-00-00'


def contact_with_phone() -> Contact:
    return Contact(email='reader@example.com', phone='+7 900 000-00-00')


@given(st.sampled_from(['basic', 'premium']))
def test_known_tier_passes_check(tier: str) -> None:
    Membership(tier=tier, valid_until=TOMORROW).check()


def test_unknown_tier_is_rejected() -> None:
    with pytest.raises(MembershipTierInvalid):
        Membership(tier='gold', valid_until=TOMORROW).check()


@given(st.text(max_size=20))
def test_any_unknown_tier_is_rejected(tier: str) -> None:
    if tier in Membership.TIER_LOAN_LIMITS:
        Membership(tier=tier, valid_until=TOMORROW).check()
    else:
        with pytest.raises(MembershipTierInvalid):
            Membership(tier=tier, valid_until=TOMORROW).check()


def test_loan_limit_depends_on_tier() -> None:
    basic = Membership(tier='basic', valid_until=TOMORROW)
    premium = Membership(tier='premium', valid_until=TOMORROW)

    assert basic.loan_limit == 3
    assert premium.loan_limit == 10


def test_membership_active_on_instance(
    reader_factory: Callable[..., Reader],
) -> None:
    assert _reader(reader_factory, valid_until=TOMORROW).membership_active(
        on=TODAY
    )
    assert _reader(reader_factory, valid_until=TODAY).membership_active(on=TODAY)
    assert not _reader(reader_factory, valid_until=YESTERDAY).membership_active(
        on=TODAY
    )


@given(
    st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)),
)
def test_membership_active_is_inclusive_of_valid_until(valid_until: date) -> None:
    reader = Reader(
        full_name='Иван Петров',
        contact=Contact(email='reader@example.com'),
        membership=Membership(tier='basic', valid_until=valid_until),
    )

    assert reader.membership_active(on=valid_until)
    assert not reader.membership_active(on=valid_until + timedelta(days=1))


def test_has_tier_and_not_blocked_on_instance(
    reader_factory: Callable[..., Reader],
) -> None:
    premium = _reader(reader_factory, tier='premium')
    blocked = _reader(reader_factory, is_blocked=True)

    assert premium.has_tier('premium')
    assert not premium.has_tier('basic')
    assert premium.not_blocked()
    assert not blocked.not_blocked()


def test_criteria_lazy_form(reader_factory: Callable[..., Reader]) -> None:
    reader = _reader(reader_factory, tier='premium', valid_until=TOMORROW)

    assert isinstance(Reader.membership_active(on=TODAY), Criteria)
    assert Reader.membership_active(on=TODAY).is_satisfied_by(reader) is True
    assert Reader.has_tier(tier='premium').is_satisfied_by(reader) is True
    assert Reader.has_tier(tier='basic').is_satisfied_by(reader) is False
    assert Reader.not_blocked().is_satisfied_by(reader) is True
    assert Reader.not_blocked().is_satisfied_by(
        _reader(reader_factory, is_blocked=True)
    ) is False


def test_criteria_combinations(reader_factory: Callable[..., Reader]) -> None:
    active_premium = _reader(
        reader_factory, tier='premium', valid_until=TOMORROW
    )
    expired_basic = _reader(
        reader_factory, tier='basic', valid_until=YESTERDAY
    )
    blocked_premium = _reader(
        reader_factory, tier='premium', is_blocked=True
    )

    can_borrow = (
        Reader.membership_active(on=TODAY)
        & Reader.not_blocked()
        & Reader.has_tier(tier='premium')
    )
    active_or_premium = Reader.membership_active(on=TODAY) | Reader.has_tier(
        tier='premium'
    )
    expired = ~Reader.membership_active(on=TODAY)

    assert can_borrow.is_satisfied_by(active_premium) is True
    assert can_borrow.is_satisfied_by(expired_basic) is False
    assert can_borrow.is_satisfied_by(blocked_premium) is False
    assert active_or_premium.is_satisfied_by(expired_basic) is False
    assert active_or_premium.is_satisfied_by(blocked_premium) is True
    assert expired.is_satisfied_by(expired_basic) is True
    assert expired.is_satisfied_by(active_premium) is False


def test_reader_not_found_message_uses_id() -> None:
    assert '7' in str(ReaderNotFound(id=7))
