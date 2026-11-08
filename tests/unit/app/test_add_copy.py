import logging

import pytest

from library.app.commands.domain.book import BookNotFound
from library.app.commands.use_cases.books.add_copy import AddCopy
from library.app.roles import Account, PermissionDenied, Permissions


def test_add_copy_appends_copy(
    in_memory_books_repo,
    test_logger,
    account,
    book_factory,
    add_copy_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    book = in_memory_books_repo.save(book_factory(copies=[]))
    usecase = AddCopy(books=in_memory_books_repo, logger=test_logger)
    usecase.run(account, add_copy_params_factory(book_id=book.id))
    saved = in_memory_books_repo.get_by_id(book.id)
    assert len(saved.copies) == 1
    assert saved.copies[0].inventory_number == 'INV-2'
    assert saved.copies[0].shelf.hall == 'B'
    record = caplog.records[0]
    assert record.msg == 'Добавлен экземпляр %r в книгу с id=%s'
    assert record.args == ('INV-2', book.id)


def test_add_copy_unknown_book(
    in_memory_books_repo,
    test_logger,
    account,
    add_copy_params_factory,
) -> None:
    usecase = AddCopy(books=in_memory_books_repo, logger=test_logger)
    with pytest.raises(BookNotFound):
        usecase.run(account, add_copy_params_factory(book_id=999))


def test_add_copy_requires_permission(
    in_memory_books_repo,
    test_logger,
    book_factory,
    add_copy_params_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory(copies=[]))
    usecase = AddCopy(books=in_memory_books_repo, logger=test_logger)
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            add_copy_params_factory(book_id=book.id),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.BOOKS_EDIT
