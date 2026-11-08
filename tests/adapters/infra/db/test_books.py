import pytest

from library.app.commands.domain.book import Book, BookNotFound, Copy, IsbnInvalid


def test_books_repo_roundtrip(
    any_books_repo,
    book_factory,
    copy_factory,
) -> None:
    book = book_factory(
        copies=[
            copy_factory(inventory_number='INV-1'),
            copy_factory(inventory_number='INV-2', is_available=False),
        ],
    )
    saved = any_books_repo.save(book)
    loaded = any_books_repo.get_by_id(saved.id)
    assert loaded == saved


def test_books_repo_update_with_copy_changes(
    any_books_repo,
    book_factory,
    copy_factory,
) -> None:
    saved = any_books_repo.save(
        book_factory(
            copies=[
                copy_factory(inventory_number='INV-1'),
                copy_factory(inventory_number='INV-2'),
            ],
        ),
    )
    loaded = any_books_repo.get_by_id(saved.id)
    loaded.title = 'Updated'
    loaded.copies = [
        Copy(
            inventory_number='INV-1',
            shelf=loaded.copies[0].shelf,
            is_available=False,
        ),
        copy_factory(inventory_number='INV-3'),
    ]
    any_books_repo.save(loaded)
    actual = any_books_repo.get_by_id(saved.id)
    assert actual.title == 'Updated'
    assert [copy.inventory_number for copy in actual.copies] == [
        'INV-1',
        'INV-3',
    ]
    assert not actual.copies[0].is_available


def test_books_repo_not_found(any_books_repo) -> None:
    with pytest.raises(BookNotFound):
        any_books_repo.get_by_id(999999)


def test_books_repo_invalid_book_is_not_saved(
    db_books_repo,
    raw_db,
    book_factory,
) -> None:
    before = raw_db.scalar('SELECT count(*) FROM library.books')
    with pytest.raises(IsbnInvalid):
        db_books_repo.save(book_factory(isbn='123'))
    after = raw_db.scalar('SELECT count(*) FROM library.books')
    assert after == before


def _saved_books(repo, book_factory, copy_factory) -> list[Book]:
    return [
        repo.save(
            book_factory(
                isbn='9780132350884',
                title='Clean Code',
                authors=['Robert Martin'],
                published_year=2008,
            ),
        ),
        repo.save(
            book_factory(
                isbn='9780201633610',
                title='Design Patterns',
                authors=['Erich Gamma'],
                published_year=1994,
                copies=[copy_factory(is_available=False)],
            ),
        ),
        repo.save(
            book_factory(
                isbn='9781491950357',
                title='Building Microservices',
                authors=['Sam Newman'],
                published_year=2015,
            ),
        ),
    ]


@pytest.mark.parametrize(
    'criteria_name',
    [
        'available',
        'published_after',
        'written_by',
        'combination',
    ],
)
def test_books_repo_find_by_criteria(
    any_books_repo,
    book_factory,
    copy_factory,
    criteria_name: str,
) -> None:
    books = _saved_books(any_books_repo, book_factory, copy_factory)
    criteria = {
        'available': Book.has_available_copies(),
        'published_after': Book.published_after(year=2000),
        'written_by': Book.written_by(author='Robert Martin'),
        'combination': (
            Book.published_after(year=2000)
            & ~Book.written_by(author='Sam Newman')
        ),
    }[criteria_name]
    expected = {
        book.id for book in books if criteria.is_satisfied_by(book)
    }
    actual = {book.id for book in any_books_repo.find(criteria)}
    assert actual == expected
