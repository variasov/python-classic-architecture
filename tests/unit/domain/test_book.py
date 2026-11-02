from datetime import date
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from library.app.commands.domain.book import (
    Book,
    CopyNotAvailable,
    CopyNotFound,
    DuplicateInventoryNumber,
    InvalidIsbn,
    PublishedInFuture,
    ShelfLocation,
    ShelfPositionInvalid,
    TitleEmpty,
)

SHELF = ShelfLocation(hall='A', rack=1, shelf=1)


def make_book(**overrides: Any) -> Book:
    fields: dict[str, Any] = {
        'isbn': '9785171183660',
        'title': 'Война и мир',
        'authors': ['Толстой'],
        'published_year': 1869,
    }
    return Book(**{**fields, **overrides})


def test_valid_book_passes_check() -> None:
    make_book().check()


@pytest.mark.parametrize(
    'isbn',
    ['', '123', '978517118366', '97851711836601', 'abcdefghijklm', '١٢٣٤٥٦٧٨٩٠١٢٣'],
)
def test_invalid_isbn(isbn: str) -> None:
    with pytest.raises(InvalidIsbn):
        make_book(isbn=isbn).check()


@given(st.text(alphabet=' \t\n', max_size=5))
def test_blank_title(title: str) -> None:
    with pytest.raises(TitleEmpty):
        make_book(title=title).check()


def test_check_published_boundary() -> None:
    make_book(published_year=2026).check_published(date(2026, 1, 1))
    with pytest.raises(PublishedInFuture):
        make_book(published_year=2027).check_published(date(2026, 12, 31))


def test_duplicate_inventory_numbers() -> None:
    book = make_book()
    book.add_copy('1', SHELF)
    book.copies.append(book.copies[0])
    with pytest.raises(DuplicateInventoryNumber):
        book.check()


def test_add_duplicate_copy() -> None:
    book = make_book()
    book.add_copy('1', SHELF)
    with pytest.raises(DuplicateInventoryNumber):
        book.add_copy('1', SHELF)


@pytest.mark.parametrize(('rack', 'shelf'), [(0, 1), (1, 0), (-1, 5)])
def test_shelf_position_invalid(rack: int, shelf: int) -> None:
    with pytest.raises(ShelfPositionInvalid):
        make_book().add_copy('1', ShelfLocation(hall='A', rack=rack, shelf=shelf))


def test_take_and_return_copy() -> None:
    book = make_book()
    book.add_copy('1', SHELF)
    book.take_copy('1')
    assert not book.copies[0].is_available
    with pytest.raises(CopyNotAvailable):
        book.take_copy('1')
    book.return_copy('1')
    assert book.copies[0].is_available


def test_unknown_copy() -> None:
    with pytest.raises(CopyNotFound):
        make_book().take_copy('404')


def test_criteria_instance_and_class_forms() -> None:
    book = make_book(authors=['Толстой', 'Иванов'])
    assert not book.has_available_copies()
    book.add_copy('1', SHELF)
    assert book.has_available_copies()
    assert Book.has_available_copies().is_satisfied_by(book)
    assert book.published_after(year=1800)
    assert not book.published_after(year=1869)
    assert Book.published_after(year=1868).is_satisfied_by(book)
    assert book.written_by(author='Иванов')
    combined = Book.written_by(author='Толстой') & ~Book.published_after(year=1900)
    assert combined.is_satisfied_by(book)
    either = Book.written_by(author='X') | Book.has_available_copies()
    assert either.is_satisfied_by(book)
