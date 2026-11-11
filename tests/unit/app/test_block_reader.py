import logging
from collections.abc import Callable

import pytest
from classic.criteria import ReturnsTrue

from library.app.commands.domain.reader import (
    Reader,
    ReaderAlreadyBlocked,
    ReaderNotFound,
    ReadersRepo,
)
from library.app.commands.use_cases.readers.block_reader import (
    BlockReader,
    BlockReaderParams,
)
from library.app.roles import Account, PermissionDenied, Permissions


@pytest.fixture
def readers_repo(in_memory_readers_repo: ReadersRepo) -> ReadersRepo:
    return in_memory_readers_repo


@pytest.fixture
def block_reader(readers_repo: ReadersRepo) -> BlockReader:
    return BlockReader(readers=readers_repo, logger=logging.getLogger('test'))


@pytest.fixture
def block_reader_params() -> Callable[..., BlockReaderParams]:
    def factory(**overrides: object) -> BlockReaderParams:
        fields: dict[str, object] = {'reader_id': 1}
        fields.update(overrides)
        return BlockReaderParams(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def no_readers_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.BOOKS_EDIT,))


@pytest.fixture
def saved_reader(
    readers_repo: ReadersRepo,
    reader_factory: Callable[..., Reader],
) -> Reader:
    return readers_repo.save(reader_factory())


def _load(repo: ReadersRepo, reader: Reader) -> Reader:
    assert reader.id is not None
    return repo.get_by_id(reader.id)


def test_blocks_reader(
    block_reader: BlockReader,
    readers_repo: ReadersRepo,
    saved_reader: Reader,
    admin: Account,
    block_reader_params: Callable[..., BlockReaderParams],
) -> None:
    block_reader.run(block_reader_params(reader_id=saved_reader.id), admin)

    assert _load(readers_repo, saved_reader).is_blocked is True


def test_missing_reader_raises(
    block_reader: BlockReader,
    readers_repo: ReadersRepo,
    admin: Account,
    block_reader_params: Callable[..., BlockReaderParams],
) -> None:
    with pytest.raises(ReaderNotFound):
        block_reader.run(block_reader_params(reader_id=987654), admin)

    assert readers_repo.find(ReturnsTrue()) == []


def test_already_blocked_reader_is_rejected(
    block_reader: BlockReader,
    readers_repo: ReadersRepo,
    reader_factory: Callable[..., Reader],
    admin: Account,
    block_reader_params: Callable[..., BlockReaderParams],
) -> None:
    reader = readers_repo.save(reader_factory(is_blocked=True))

    with pytest.raises(ReaderAlreadyBlocked):
        block_reader.run(block_reader_params(reader_id=reader.id), admin)

    assert _load(readers_repo, reader).is_blocked is True


def test_requires_permission_before_storage(
    block_reader: BlockReader,
    readers_repo: ReadersRepo,
    saved_reader: Reader,
    no_readers_permission: Account,
    block_reader_params: Callable[..., BlockReaderParams],
) -> None:
    with pytest.raises(PermissionDenied):
        block_reader.run(
            block_reader_params(reader_id=987654),
            no_readers_permission,
        )

    assert _load(readers_repo, saved_reader).is_blocked is False
