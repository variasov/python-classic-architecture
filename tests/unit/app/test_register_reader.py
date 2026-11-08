import logging

import pytest

from library.app.commands.domain.reader import (
    ContactEmailInvalid,
    MembershipTierInvalid,
    ReaderNotFound,
)
from library.app.commands.use_cases.readers.register_reader import (
    RegisterReader,
)
from library.app.roles import Account, PermissionDenied, Permissions


def test_register_reader_saves_reader(
    in_memory_readers_repo,
    test_logger,
    account,
    register_reader_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    usecase = RegisterReader(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    params = register_reader_params_factory(phone='+79990000000')
    reader_id = usecase.run(account, params)
    saved = in_memory_readers_repo.get_by_id(reader_id)
    assert saved.full_name == 'Иван Иванов'
    assert saved.contact.email == 'ivan@example.com'
    assert saved.contact.phone == '+79990000000'
    assert saved.membership.tier == 'basic'
    assert saved.membership.valid_until == params.valid_until
    record = caplog.records[0]
    assert record.msg == 'Зарегистрирован читатель %r'
    assert record.args == ('Иван Иванов',)


def test_register_reader_invalid_email(
    in_memory_readers_repo,
    test_logger,
    account,
    register_reader_params_factory,
) -> None:
    usecase = RegisterReader(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    with pytest.raises(ContactEmailInvalid):
        usecase.run(
            account,
            register_reader_params_factory(email='invalid'),
        )


def test_register_reader_invalid_tier(
    in_memory_readers_repo,
    test_logger,
    account,
    register_reader_params_factory,
) -> None:
    usecase = RegisterReader(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    with pytest.raises(MembershipTierInvalid):
        usecase.run(
            account,
            register_reader_params_factory(tier='vip'),
        )


def test_register_reader_requires_permission(
    in_memory_readers_repo,
    test_logger,
    register_reader_params_factory,
) -> None:
    usecase = RegisterReader(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            register_reader_params_factory(),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.READERS_EDIT
    with pytest.raises(ReaderNotFound):
        in_memory_readers_repo.get_by_id(1)
