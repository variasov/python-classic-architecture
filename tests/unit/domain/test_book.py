import pytest
from hypothesis import given
from hypothesis import strategies as st

from library.app.commands.domain.book import (
    Book,
    BookTitleEmpty,
    CopyNotAvailable,
    CopyNotFound,
    DuplicateInventoryNumber,
    IsbnInvalid,
    PublishedYearInFuture,
    ShelfLocation,
    ShelfRackInvalid,
    ShelfShelfInvalid,
)


def test_valid_book_passes_check(book_factory) -> None:
    book_factory().check(current_year=2026)


def test_isbn_must_have_13_digits(book_factory) -> None:
    with pytest.raises(IsbnInvalid) as exc_info:
        book_factory(isbn='123').check(current_year=2026)
    assert exc_info.value.isbn == '123'


def test_isbn_with_letters_is_invalid(book_factory) -> None:
    with pytest.raises(IsbnInvalid):
        book_factory(isbn='978013235088X').check(current_year=2026)


@given(
    st.text(alphabet='0123456789', min_size=0, max_size=20).filter(
        lambda value: len(value) != 13,
    ),
)
def test_any_wrong_length_isbn_is_invalid(isbn: str) -> None:
    with pytest.raises(IsbnInvalid):
        Book(
            isbn=isbn,
            title='Title',
            authors=['Author'],
            published_year=2000,
        ).check(current_year=2026)


@given(st.text(alphabet=' \t', min_size=1, max_size=5))
def test_whitespace_title_is_invalid(title: str) -> None:
    book = Book(
        isbn='9780132350884',
        title=title,
        authors=['Author'],
        published_year=2000,
    )
    with pytest.raises(BookTitleEmpty):
        book.check(current_year=2026)


def test_empty_title_is_invalid(book_factory) -> None:
    with pytest.raises(BookTitleEmpty) as exc_info:
        book_factory(title='').check(current_year=2026)
    expected = 'Название книги не может быть пустым'
    assert str(exc_info.value) == expected


@given(st.integers(min_value=2027, max_value=3000))
def test_published_year_in_future_is_invalid(year: int) -> None:
    book = Book(
        isbn='9780132350884',
        title='Title',
        authors=['Author'],
        published_year=year,
    )
    with pytest.raises(PublishedYearInFuture) as exc_info:
        book.check(current_year=2026)
    assert exc_info.value.year == year
    assert exc_info.value.current_year == 2026


def test_published_year_on_boundary_is_valid(book_factory) -> None:
    book_factory(published_year=2026).check(current_year=2026)


def test_duplicate_inventory_numbers_are_invalid(
    book_factory,
    copy_factory,
) -> None:
    book = book_factory(
        copies=[
            copy_factory(inventory_number='INV-1'),
            copy_factory(inventory_number='INV-1'),
        ],
    )
    with pytest.raises(DuplicateInventoryNumber) as exc_info:
        book.check(current_year=2026)
    assert exc_info.value.inventory_number == 'INV-1'


def test_shelf_rack_must_be_positive() -> None:
    with pytest.raises(ShelfRackInvalid) as exc_info:
        ShelfLocation(hall='A', rack=0, shelf=1).check()
    assert exc_info.value.rack == 0


def test_shelf_number_must_be_positive() -> None:
    with pytest.raises(ShelfShelfInvalid) as exc_info:
        ShelfLocation(hall='A', rack=1, shelf=0).check()
    assert exc_info.value.shelf == 0


def test_book_check_calls_copy_check(book_factory, copy_factory) -> None:
    book = book_factory(
        copies=[
            copy_factory(
                shelf=ShelfLocation(hall='A', rack=0, shelf=1),
            ),
        ],
    )
    with pytest.raises(ShelfRackInvalid) as exc_info:
        book.check(current_year=2026)
    assert exc_info.value.rack == 0


def test_add_copy_appends_copy(book_factory, shelf_location_factory) -> None:
    book = book_factory(copies=[])
    book.add_copy(
        inventory_number='INV-1',
        shelf=shelf_location_factory(hall='B', rack=2, shelf=3),
    )
    assert len(book.copies) == 1
    assert book.copies[0].inventory_number == 'INV-1'
    assert book.copies[0].is_available


def test_take_copy_marks_it_unavailable(book_factory) -> None:
    book = book_factory()
    book.take_copy('INV-1')
    assert book.copies[0].is_available is False


def test_take_unavailable_copy_raises(book_factory, copy_factory) -> None:
    book = book_factory(
        id=7,
        copies=[copy_factory(is_available=False)],
    )
    with pytest.raises(CopyNotAvailable) as exc_info:
        book.take_copy('INV-1')
    assert exc_info.value.book_id == 7
    assert exc_info.value.inventory_number == 'INV-1'


def test_take_missing_copy_raises(book_factory) -> None:
    with pytest.raises(CopyNotFound) as exc_info:
        book_factory(id=7).take_copy('MISSING')
    assert exc_info.value.book_id == 7
    assert exc_info.value.inventory_number == 'MISSING'


def test_return_copy_marks_it_available(book_factory, copy_factory) -> None:
    book = book_factory(copies=[copy_factory(is_available=False)])
    book.return_copy('INV-1')
    assert book.copies[0].is_available is True


def test_return_missing_copy_raises(book_factory) -> None:
    with pytest.raises(CopyNotFound) as exc_info:
        book_factory().return_copy('MISSING')
    assert exc_info.value.inventory_number == 'MISSING'


def test_has_available_copies_in_both_forms(
    book_factory,
    copy_factory,
) -> None:
    available = book_factory()
    unavailable = book_factory(
        copies=[copy_factory(is_available=False)],
    )
    assert available.has_available_copies()
    assert Book.has_available_copies().is_satisfied_by(available)
    assert not unavailable.has_available_copies()
    assert not Book.has_available_copies().is_satisfied_by(unavailable)


def test_published_after_in_both_forms(book_factory) -> None:
    book = book_factory(published_year=2000)
    assert book.published_after(year=1999)
    assert not book.published_after(year=2000)
    assert Book.published_after(year=1999).is_satisfied_by(book)


def test_written_by_in_both_forms(book_factory) -> None:
    book = book_factory(authors=['Alice', 'Bob'])
    assert book.written_by(author='Alice')
    assert not book.written_by(author='Carol')
    assert Book.written_by(author='Bob').is_satisfied_by(book)


def test_book_criteria_combinations(book_factory) -> None:
    book = book_factory(published_year=2000, authors=['Alice'])
    combined = (
        Book.published_after(year=1990)
        & Book.written_by(author='Alice')
        & ~Book.published_after(year=2010)
    )
    assert combined.is_satisfied_by(book)
    either = Book.published_after(year=2010) | Book.written_by(
        author='Alice',
    )
    assert either.is_satisfied_by(book)
    available_or_recent = (
        Book.published_after(year=2010) | Book.has_available_copies()
    )
    assert available_or_recent.is_satisfied_by(book)


def test_published_year_check_can_be_skipped(book_factory) -> None:
    book_factory(published_year=3000).check()


def test_shelf_location_is_frozen() -> None:
    location = ShelfLocation(hall='A', rack=1, shelf=1)
    with pytest.raises(AttributeError):
        location.rack = 2  # type: ignore[misc]


def test_book_defaults_id_is_none(book_factory) -> None:
    assert book_factory().id is None
