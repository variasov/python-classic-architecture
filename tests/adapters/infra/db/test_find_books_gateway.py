from library.app.queries.books.find_books import FindBooksParams
from library.infra.db.repos.books import BooksRepository


def _seed(books_repo: BooksRepository, book_factory, copy_factory) -> None:
    books_repo.save(
        book_factory(
            isbn='9780132350884',
            title='Clean Code',
            authors=['Robert Martin'],
            published_year=2008,
        ),
    )
    books_repo.save(
        book_factory(
            isbn='9780201633610',
            title='Design Patterns',
            authors=['Erich Gamma'],
            published_year=1994,
            copies=[copy_factory(is_available=False)],
        ),
    )
    books_repo.save(
        book_factory(
            isbn='9781491950357',
            title='Building Microservices',
            authors=['Sam Newman'],
            published_year=2015,
        ),
    )


def test_find_books_no_filters(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    result = find_books_gateway_db.find(FindBooksParams())
    assert [book.title for book in result] == [
        'Building Microservices',
        'Clean Code',
        'Design Patterns',
    ]


def test_find_books_title_filter(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    result = find_books_gateway_db.find(
        FindBooksParams(title__contains='clean'),
    )
    assert [book.title for book in result] == ['Clean Code']


def test_find_books_author_filter(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    result = find_books_gateway_db.find(
        FindBooksParams(author='Sam Newman'),
    )
    assert [book.title for book in result] == ['Building Microservices']


def test_find_books_only_available(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    result = find_books_gateway_db.find(
        FindBooksParams(only_available=True),
    )
    assert [book.title for book in result] == [
        'Building Microservices',
        'Clean Code',
    ]


def test_find_books_year_filters(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    recent = find_books_gateway_db.find(
        FindBooksParams(year_from=2000),
    )
    old = find_books_gateway_db.find(FindBooksParams(year_to=2000))
    assert [book.title for book in recent] == [
        'Building Microservices',
        'Clean Code',
    ]
    assert [book.title for book in old] == ['Design Patterns']


def test_find_books_combined_filters(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    result = find_books_gateway_db.find(
        FindBooksParams(
            author='Robert Martin',
            only_available=True,
            year_from=2000,
            year_to=2010,
        ),
    )
    assert [book.title for book in result] == ['Clean Code']


def test_find_books_sorting(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    by_year = find_books_gateway_db.find(
        FindBooksParams(sort_by='published_year', sort_order='desc'),
    )
    assert [book.published_year for book in by_year] == [2015, 2008, 1994]
    by_title_desc = find_books_gateway_db.find(
        FindBooksParams(sort_by='title', sort_order='desc'),
    )
    assert [book.title for book in by_title_desc] == [
        'Design Patterns',
        'Clean Code',
        'Building Microservices',
    ]


def test_find_books_pagination(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    result = find_books_gateway_db.find(
        FindBooksParams(limit=1, offset=1),
    )
    assert [book.title for book in result] == ['Clean Code']


def test_find_books_empty_result(find_books_gateway_db) -> None:
    assert find_books_gateway_db.find(FindBooksParams()) == []


def test_find_books_maps_dto(
    find_books_gateway_db,
    db_books_repo,
    book_factory,
    copy_factory,
) -> None:
    _seed(db_books_repo, book_factory, copy_factory)
    result = find_books_gateway_db.find(
        FindBooksParams(title__contains='Clean'),
    )
    assert result[0].isbn == '9780132350884'
    assert result[0].authors == ['Robert Martin']
    assert result[0].published_year == 2008
