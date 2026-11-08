import logging
from datetime import date

import pytest

from library.app.commands.domain.book import (
    BookNotInCatalog,
    PublishedYearInFuture,
)
from library.app.commands.isbn_catalog import CatalogBook
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
)
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date(2026, 3, 10)


def _usecase(books, catalog, clock_factory, test_logger) -> CreateBookFromCatalog:
    return CreateBookFromCatalog(
        books=books,
        catalog=catalog,
        clock=clock_factory(TODAY),
        logger=test_logger,
    )


def test_create_book_from_catalog_saves_book(
    in_memory_books_repo,
    isbn_catalog,
    clock_factory,
    test_logger,
    account,
    create_book_from_catalog_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    isbn_catalog.books['9780132350884'] = CatalogBook(
        isbn='9780132350884',
        title='Clean Code',
        authors=['Robert Martin'],
        year=2008,
    )
    usecase = _usecase(
        in_memory_books_repo,
        isbn_catalog,
        clock_factory,
        test_logger,
    )
    book_id = usecase.run(
        account,
        create_book_from_catalog_params_factory(),
    )
    saved = in_memory_books_repo.get_by_id(book_id)
    assert saved.title == 'Clean Code'
    assert saved.authors == ['Robert Martin']
    assert saved.published_year == 2008
    record = caplog.records[0]
    assert record.msg == 'Создана книга из каталога %r'
    assert record.args == ('9780132350884',)


def test_create_book_from_catalog_rejects_future_year(
    in_memory_books_repo,
    isbn_catalog,
    clock_factory,
    test_logger,
    account,
    create_book_from_catalog_params_factory,
) -> None:
    isbn_catalog.books['9780132350884'] = CatalogBook(
        isbn='9780132350884',
        title='Clean Code',
        authors=['Robert Martin'],
        year=2027,
    )
    usecase = _usecase(
        in_memory_books_repo,
        isbn_catalog,
        clock_factory,
        test_logger,
    )
    with pytest.raises(PublishedYearInFuture):
        usecase.run(
            account,
            create_book_from_catalog_params_factory(),
        )


def test_create_book_from_catalog_missing_book(
    in_memory_books_repo,
    isbn_catalog,
    clock_factory,
    test_logger,
    account,
    create_book_from_catalog_params_factory,
) -> None:
    usecase = _usecase(
        in_memory_books_repo,
        isbn_catalog,
        clock_factory,
        test_logger,
    )
    with pytest.raises(BookNotInCatalog) as exc_info:
        usecase.run(account, create_book_from_catalog_params_factory())
    assert exc_info.value.isbn == '9780132350884'


def test_create_book_from_catalog_requires_permission(
    in_memory_books_repo,
    isbn_catalog,
    clock_factory,
    test_logger,
    create_book_from_catalog_params_factory,
) -> None:
    usecase = _usecase(
        in_memory_books_repo,
        isbn_catalog,
        clock_factory,
        test_logger,
    )
    isbn_catalog.books['9780132350884'] = CatalogBook(
        isbn='9780132350884',
        title='Clean Code',
        authors=['Robert Martin'],
        year=2008,
    )
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            create_book_from_catalog_params_factory(),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.BOOKS_EDIT
