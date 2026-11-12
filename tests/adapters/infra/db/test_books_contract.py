from collections.abc import Callable

import pytest

from library.app.domain.book import Book, BookNotFound, BooksRepo


def _load(repo: BooksRepo, book: Book) -> Book:
    assert book.id is not None
    return repo.get_by_id(book.id)


def test_saved_book_is_read_back(
    any_books_repo: BooksRepo,
    book_factory: Callable[..., Book],
) -> None:
    book = any_books_repo.save(book_factory())

    loaded = _load(any_books_repo, book)

    assert loaded == book


def test_authors_keep_their_order(
    any_books_repo: BooksRepo,
    book_factory: Callable[..., Book],
) -> None:
    book = any_books_repo.save(
        book_factory(authors=['Первый', 'Второй', 'Третий']),
    )

    loaded = _load(any_books_repo, book)

    assert loaded.authors == ['Первый', 'Второй', 'Третий']


def test_update_replaces_authors(
    any_books_repo: BooksRepo,
    book_factory: Callable[..., Book],
) -> None:
    book = any_books_repo.save(book_factory())
    book.title = 'Анна Каренина'
    book.authors = ['Лев Толстой', 'Новый Автор']
    any_books_repo.save(book)

    loaded = _load(any_books_repo, book)

    assert loaded.title == 'Анна Каренина'
    assert loaded.authors == ['Лев Толстой', 'Новый Автор']


def test_get_missing_book_raises(any_books_repo: BooksRepo) -> None:
    with pytest.raises(BookNotFound):
        any_books_repo.get_by_id(987654)


def test_save_invalid_book_writes_nothing(
    any_books_repo: BooksRepo,
    book_factory: Callable[..., Book],
) -> None:
    with pytest.raises(Exception):
        any_books_repo.save(book_factory(isbn='bad'))

    assert any_books_repo.find(Book.written_by(author='Лев Толстой')) == []
