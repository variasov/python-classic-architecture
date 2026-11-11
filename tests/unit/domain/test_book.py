from collections.abc import Callable
from datetime import date

import pytest
from classic.criteria import Criteria

from library.app.commands.domain.book import (
    Book,
    BookIsbnInvalid,
    BookNotFound,
    BookPublishedInFuture,
    BookTitleEmpty,
)


def test_valid_book_passes_check(book_factory: Callable[..., Book]) -> None:
    book_factory().check()


def test_isbn_must_have_13_digits(book_factory: Callable[..., Book]) -> None:
    with pytest.raises(BookIsbnInvalid):
        book_factory(isbn='123').check()
    with pytest.raises(BookIsbnInvalid):
        book_factory(isbn='978517118366X').check()


def test_empty_title_is_rejected(book_factory: Callable[..., Book]) -> None:
    with pytest.raises(BookTitleEmpty):
        book_factory(title='   ').check()


def test_published_year_cannot_be_in_the_future(
    book_factory: Callable[..., Book],
) -> None:
    with pytest.raises(BookPublishedInFuture):
        book_factory(published_year=date.today().year + 1).check()


def test_criteria_on_instance(book_factory: Callable[..., Book]) -> None:
    book = book_factory(published_year=2000, authors=['Иван Бунин'])

    assert book.published_after(1999) is True
    assert book.published_after(2000) is False
    assert book.written_by('Иван Бунин') is True
    assert book.written_by('Лев Толстой') is False


def test_criteria_lazy_form(book_factory: Callable[..., Book]) -> None:
    book = book_factory(published_year=2000, authors=['Иван Бунин'])

    assert Book.published_after(year=1999).is_satisfied_by(book) is True
    assert Book.published_after(year=2000).is_satisfied_by(book) is False
    assert Book.written_by(author='Иван Бунин').is_satisfied_by(book) is True


def test_criteria_combinations(book_factory: Callable[..., Book]) -> None:
    book = book_factory(published_year=2000, authors=['Иван Бунин'])
    old_or_bunin = Book.published_after(year=1999) | Book.written_by(
        author='Иван Бунин',
    )
    both = Book.published_after(year=1999) & Book.written_by(author='Иван Бунин')
    not_bunin = ~Book.written_by(author='Иван Бунин')

    assert isinstance(old_or_bunin, Criteria)
    assert old_or_bunin.is_satisfied_by(book) is True
    assert both.is_satisfied_by(book) is True
    assert not_bunin.is_satisfied_by(book) is False


def test_book_not_found_message_uses_id() -> None:
    error = BookNotFound(id=7)

    assert '7' in str(error)
