import logging
from collections.abc import Callable

import pytest
from classic.criteria import ReturnsTrue

from library.app.commands.domain.reader import (
    Reader,
    ReaderNotBlocked,
    ReaderNotFound,
    ReadersRepo,
)
from library.app.commands.use_cases.readers.unblock_reader import (
    UnblockReader,
    UnblockReaderParams,
)
from library.app.roles import Account, PermissionDenied, Permissions


@pytest.fixture
def readers_repo(in_memory_readers_repo: ReadersRepo) -> ReadersRepo:
    return in_memory_readers_repo


@pytest.fixture
def unblock_reader(readers_repo: ReadersRepo) -> UnblockReader:
    return UnblockReader(readers=readers_repo, logger=logging.getLogger('test'))


@pytest.fixture
def unblock_reader_params() -> Callable[..., UnblockReaderParams]:
    def factory(**overrides: object) -> UnblockReaderParams:
        fields: dict[str, object] = {'reader_id': 1}
        fields.update(overrides)
        return UnblockReaderParams(**fields)  # type: ignore[arg-type]

    return factory


@pytest.fixture
def no_readers_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.BOOKS_EDIT,))


@pytest.fixture
def blocked_reader(
    readers_repo: ReadersRepo,
    reader_factory: Callable[..., Reader],
) -> Reader:
    return readers_repo.save(reader_factory(is_blocked=True))


def _load(repo: ReadersRepo, reader: Reader) -> Reader:
    assert reader.id is not None
    return repo.get_by_id(reader.id)


def test_unblocks_reader(
    unblock_reader: UnblockReader,
    readers_repo: ReadersRepo,
    blocked_reader: Reader,
    admin: Account,
    unblock_reader_params: Callable[..., UnblockReaderParams],
) -> None:
    unblock_reader.run(
        unblock_reader_params(reader_id=blocked_reader.id),
        admin,
    )

    assert _load(readers_repo, blocked_reader).is_blocked is False


def test_missing_reader_raises(
    unblock_reader: UnblockReader,
    readers_repo: ReadersRepo,
    admin: Account,
    unblock_reader_params: Callable[..., UnblockReaderParams],
) -> None:
    with pytest.raises(ReaderNotFound):
        unblock_reader.run(unblock_reader_params(reader_id=987654), admin)

    assert readers_repo.find(ReturnsTrue()) == []


def test_not_blocked_reader_is_rejected(
    unblock_reader: UnblockReader,
    readers_repo: ReadersRepo,
    reader_factory: Callable[..., Reader],
    admin: Account,
    unblock_reader_params: Callable[..., UnblockReaderParams],
) -> None:
    reader = readers_repo.save(reader_factory())

    with pytest.raises(ReaderNotBlocked):
        unblock_reader.run(unblock_reader_params(reader_id=reader.id), admin)

    assert _load(readers_repo, reader).is_blocked is False


def test_requires_permission_before_storage(
    unblock_reader: UnblockReader,
    readers_repo: ReadersRepo,
    blocked_reader: Reader,
    no_readers_permission: Account,
    unblock_reader_params: Callable[..., UnblockReaderParams],
) -> None:
    with pytest.raises(PermissionDenied):
        unblock_reader.run(
            unblock_reader_params(reader_id=987654),
            no_readers_permission,
        )

    assert _load(readers_repo, blocked_reader).is_blocked is True
