import logging
from datetime import date

import pytest

from library.app.commands.domain.reader import ReaderNotFound
from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
)
from library.app.roles import Account, PermissionDenied, Permissions


def test_extend_membership_updates_reader(
    in_memory_readers_repo,
    test_logger,
    account,
    reader_factory,
    extend_membership_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = ExtendMembership(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    usecase.run(
        account,
        extend_membership_params_factory(
            reader_id=reader.id,
            until=date(2030, 1, 1),
        ),
    )
    saved = in_memory_readers_repo.get_by_id(reader.id)
    assert saved.membership.valid_until == date(2030, 1, 1)
    assert saved.membership.tier == 'basic'
    record = caplog.records[0]
    assert record.msg == 'Продлено членство читателя с id=%s'
    assert record.args == (reader.id,)


def test_extend_membership_unknown_reader(
    in_memory_readers_repo,
    test_logger,
    account,
    extend_membership_params_factory,
) -> None:
    usecase = ExtendMembership(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    with pytest.raises(ReaderNotFound):
        usecase.run(account, extend_membership_params_factory())


def test_extend_membership_requires_permission(
    in_memory_readers_repo,
    test_logger,
    reader_factory,
    extend_membership_params_factory,
) -> None:
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = ExtendMembership(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            extend_membership_params_factory(reader_id=reader.id),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.READERS_EDIT
