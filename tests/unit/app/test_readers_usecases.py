import logging
from collections.abc import Callable
from datetime import date

import pytest
from library.app.commands.domain.reader import (
    InvalidEmail,
    MembershipNotExtended,
    ReaderNotFound,
    ReadersRepo,
)
from library.app.commands.use_cases.readers.block_reader import (
    BlockReader,
    BlockReaderParams,
)
from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
    ExtendMembershipParams,
)
from library.app.commands.use_cases.readers.register_reader import (
    RegisterReader,
    RegisterReaderParams,
)
from library.app.roles import Account, PermissionDenied


def test_register_reader(
    in_memory_readers_repo: ReadersRepo,
    logger: logging.Logger,
    admin: Account,
    today: date,
) -> None:
    register = RegisterReader(readers=in_memory_readers_repo, logger=logger)
    params = RegisterReaderParams(
        full_name='Иван',
        email='i@e.com',
        tier='premium',
        valid_until=today,
    )
    reader_id = register.run(params, admin)
    reader = in_memory_readers_repo.get_by_id(reader_id)
    assert reader.membership.loan_limit == 10
    assert reader.contact.phone is None


def test_register_reader_invalid_email(
    in_memory_readers_repo: ReadersRepo,
    logger: logging.Logger,
    admin: Account,
    today: date,
) -> None:
    register = RegisterReader(readers=in_memory_readers_repo, logger=logger)
    params = RegisterReaderParams(
        full_name='Иван',
        email='bad',
        tier='basic',
        valid_until=today,
    )
    with pytest.raises(InvalidEmail):
        register.run(params, admin)


def test_register_reader_permission_denied(
    in_memory_readers_repo: ReadersRepo,
    logger: logging.Logger,
    guest: Account,
    today: date,
) -> None:
    register = RegisterReader(readers=in_memory_readers_repo, logger=logger)
    params = RegisterReaderParams(
        full_name='Иван',
        email='i@e.com',
        tier='basic',
        valid_until=today,
    )
    with pytest.raises(PermissionDenied):
        register.run(params, guest)


def test_extend_membership(
    in_memory_readers_repo: ReadersRepo,
    logger: logging.Logger,
    add_reader: Callable[..., int],
    admin: Account,
    today: date,
) -> None:
    reader_id = add_reader()
    extend = ExtendMembership(readers=in_memory_readers_repo, logger=logger)
    with pytest.raises(MembershipNotExtended):
        extend.run(ExtendMembershipParams(reader_id=reader_id, until=today), admin)
    new_date = date(2027, 1, 1)
    extend.run(ExtendMembershipParams(reader_id=reader_id, until=new_date), admin)
    assert (
        in_memory_readers_repo.get_by_id(reader_id).membership.valid_until == new_date
    )


def test_block_reader(
    in_memory_readers_repo: ReadersRepo,
    logger: logging.Logger,
    add_reader: Callable[..., int],
    admin: Account,
    guest: Account,
) -> None:
    reader_id = add_reader()
    block = BlockReader(readers=in_memory_readers_repo, logger=logger)
    with pytest.raises(PermissionDenied):
        block.run(BlockReaderParams(reader_id=reader_id), guest)
    assert not in_memory_readers_repo.get_by_id(reader_id).is_blocked
    block.run(BlockReaderParams(reader_id=reader_id), admin)
    assert in_memory_readers_repo.get_by_id(reader_id).is_blocked


def test_block_unknown_reader(
    in_memory_readers_repo: ReadersRepo,
    logger: logging.Logger,
    admin: Account,
) -> None:
    block = BlockReader(readers=in_memory_readers_repo, logger=logger)
    with pytest.raises(ReaderNotFound):
        block.run(BlockReaderParams(reader_id=404), admin)
