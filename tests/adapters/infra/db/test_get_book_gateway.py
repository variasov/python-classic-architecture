from library.infra.db.repos.books import BooksRepository


def test_get_book_gateway_returns_card(
    get_book_gateway_db,
    db_books_repo: BooksRepository,
    book_factory,
    copy_factory,
) -> None:
    book = db_books_repo.save(
        book_factory(
            copies=[
                copy_factory(inventory_number='INV-1'),
                copy_factory(
                    inventory_number='INV-2',
                    shelf=copy_factory().shelf.__class__(
                        hall='B',
                        rack=2,
                        shelf=3,
                    ),
                ),
            ],
        ),
    )
    card = get_book_gateway_db.get(book.id)
    assert card is not None
    assert card.id == book.id
    assert [copy.inventory_number for copy in card.copies] == [
        'INV-1',
        'INV-2',
    ]
    assert card.copies[1].hall == 'B'
    assert card.copies[1].rack == 2
    assert card.copies[1].shelf == 3


def test_get_book_gateway_not_found(get_book_gateway_db) -> None:
    assert get_book_gateway_db.get(999999) is None


def test_get_book_gateway_without_copies(
    get_book_gateway_db,
    db_books_repo: BooksRepository,
    book_factory,
) -> None:
    book = db_books_repo.save(book_factory(copies=[]))
    card = get_book_gateway_db.get(book.id)
    assert card is not None
    assert card.copies == []
