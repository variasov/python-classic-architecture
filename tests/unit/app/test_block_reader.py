import logging

import pytest

from library.app.commands.domain.reader import ReaderNotFound
from library.app.commands.use_cases.readers.block_reader import BlockReader
from library.app.roles import Account, PermissionDenied, Permissions


def test_block_reader_blocks_reader(
    in_memory_readers_repo,
    test_logger,
    account,
    reader_factory,
    block_reader_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = BlockReader(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    usecase.run(account, block_reader_params_factory(reader_id=reader.id))
    assert in_memory_readers_repo.get_by_id(reader.id).is_blocked is True
    record = caplog.records[0]
    assert record.msg == 'Заблокирован читатель с id=%s'
    assert record.args == (reader.id,)


def test_block_reader_unknown_reader(
    in_memory_readers_repo,
    test_logger,
    account,
    block_reader_params_factory,
) -> None:
    usecase = BlockReader(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    with pytest.raises(ReaderNotFound):
        usecase.run(account, block_reader_params_factory())


def test_block_reader_requires_permission(
    in_memory_readers_repo,
    test_logger,
    reader_factory,
    block_reader_params_factory,
) -> None:
    reader = in_memory_readers_repo.save(reader_factory())
    usecase = BlockReader(
        readers=in_memory_readers_repo,
        logger=test_logger,
    )
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            block_reader_params_factory(reader_id=reader.id),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.READERS_EDIT
