import logging
from collections.abc import Callable
from datetime import date

import pytest
from classic.criteria import ReturnsTrue

from library.app.commands.domain.reader import (
    Contact,
    ContactEmailInvalid,
    Membership,
    ReadersRepo,
)
from library.app.commands.use_cases.readers.register_reader import (
    RegisterReader,
    RegisterReaderParams,
)
from library.app.roles import Account, PermissionDenied, Permissions

VALID_UNTIL = date(2027, 1, 31)


@pytest.fixture
def readers_repo(in_memory_readers_repo: ReadersRepo) -> ReadersRepo:
    return in_memory_readers_repo


@pytest.fixture
def register_reader(readers_repo: ReadersRepo) -> RegisterReader:
    return RegisterReader(readers=readers_repo, logger=logging.getLogger('test'))


@pytest.fixture
def register_reader_params() -> Callable[..., RegisterReaderParams]:
    def factory(**overrides: object) -> RegisterReaderParams:
        fields: dict[str, object] = {
            'full_name': 'Иван Петров',
            'email': 'ivan@example.com',
            'phone': '+7 900 000-00-00',
            'tier': 'premium',
            'valid_until': VALID_UNTIL,
        }
        fields.update(overrides)
        return RegisterReaderParams(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def no_readers_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.BOOKS_EDIT,))


def test_registers_reader(
    register_reader: RegisterReader,
    readers_repo: ReadersRepo,
    admin: Account,
    register_reader_params: Callable[..., RegisterReaderParams],
) -> None:
    reader_id = register_reader.run(register_reader_params(), admin)

    saved = readers_repo.get_by_id(reader_id)
    assert saved.full_name == 'Иван Петров'
    assert saved.contact == Contact(
        email='ivan@example.com',
        phone='+7 900 000-00-00',
    )
    assert saved.membership == Membership(tier='premium', valid_until=VALID_UNTIL)
    assert saved.is_blocked is False


def test_phone_can_be_absent(
    register_reader: RegisterReader,
    readers_repo: ReadersRepo,
    admin: Account,
    register_reader_params: Callable[..., RegisterReaderParams],
) -> None:
    reader_id = register_reader.run(register_reader_params(phone=None), admin)

    assert readers_repo.get_by_id(reader_id).contact.phone is None


def test_requires_permission(
    register_reader: RegisterReader,
    readers_repo: ReadersRepo,
    no_readers_permission: Account,
    register_reader_params: Callable[..., RegisterReaderParams],
) -> None:
    with pytest.raises(PermissionDenied):
        register_reader.run(register_reader_params(), no_readers_permission)

    assert readers_repo.find(ReturnsTrue()) == []


def test_domain_invariants_are_not_skipped(
    register_reader: RegisterReader,
    readers_repo: ReadersRepo,
    admin: Account,
    register_reader_params: Callable[..., RegisterReaderParams],
) -> None:
    with pytest.raises(ContactEmailInvalid):
        register_reader.run(
            register_reader_params(email='ivan.example.com'),
            admin,
        )

    assert readers_repo.find(ReturnsTrue()) == []


def test_params_accept_values_without_extra_checks(
    register_reader_params: Callable[..., RegisterReaderParams],
) -> None:
    params = register_reader_params(
        full_name='',
        email='not-an-email',
        phone=None,
        tier='unknown',
    )

    assert params.full_name == ''
    assert params.email == 'not-an-email'
    assert params.phone is None
    assert params.tier == 'unknown'
    assert params.valid_until == VALID_UNTIL
