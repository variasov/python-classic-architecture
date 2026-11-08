import logging
from datetime import date

import pytest

from library.app.commands.domain.book import (
    BookNotFound,
    IsbnInvalid,
    PublishedYearInFuture,
)
from library.app.commands.use_cases.books.create_book import CreateBook
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date(2026, 3, 10)


def _usecase(books, clock_factory, test_logger) -> CreateBook:
    return CreateBook(
        books=books,
        clock=clock_factory(TODAY),
        logger=test_logger,
    )


def test_create_book_saves_book(
    in_memory_books_repo,
    clock_factory,
    test_logger,
    account,
    create_book_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    usecase = _usecase(in_memory_books_repo, clock_factory, test_logger)
    book_id = usecase.run(account, create_book_params_factory())
    saved = in_memory_books_repo.get_by_id(book_id)
    assert saved.title == 'Clean Code'
    assert saved.isbn == '9780132350884'
    assert saved.authors == ['Robert Martin']
    record = caplog.records[0]
    assert record.msg == 'Создана книга %r с id=%s'
    assert record.args == ('Clean Code', book_id)


def test_create_book_requires_permission(
    in_memory_books_repo,
    clock_factory,
    test_logger,
    create_book_params_factory,
) -> None:
    usecase = _usecase(in_memory_books_repo, clock_factory, test_logger)
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            create_book_params_factory(),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.BOOKS_EDIT
    with pytest.raises(BookNotFound):
        in_memory_books_repo.get_by_id(1)


def test_create_book_rejects_future_year(
    in_memory_books_repo,
    clock_factory,
    test_logger,
    account,
    create_book_params_factory,
) -> None:
    usecase = _usecase(in_memory_books_repo, clock_factory, test_logger)
    with pytest.raises(PublishedYearInFuture):
        usecase.run(
            account,
            create_book_params_factory(published_year=2027),
        )


def test_create_book_rejects_invalid_isbn(
    in_memory_books_repo,
    clock_factory,
    test_logger,
    account,
    create_book_params_factory,
) -> None:
    usecase = _usecase(in_memory_books_repo, clock_factory, test_logger)
    with pytest.raises(IsbnInvalid):
        usecase.run(account, create_book_params_factory(isbn='123'))
