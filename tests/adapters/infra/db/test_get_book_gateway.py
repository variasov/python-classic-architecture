from collections.abc import Callable

from library.app.commands.domain.book import Book, BooksRepo
from library.app.commands.domain.copy import CopiesRepo, Copy, ShelfLocation
from library.app.queries.books.get_book import GetBookGateway, GetBookParams


def test_card_contains_book_and_copies(
    db_get_book_gateway: GetBookGateway,
    db_books_repo: BooksRepo,
    db_copies_repo: CopiesRepo,
    book_factory: Callable[..., Book],
    copy_factory: Callable[..., Copy],
) -> None:
    book = db_books_repo.save(
        book_factory(authors=['Лев Толстой', 'Второй автор']),
    )
    assert book.id is not None
    first = db_copies_repo.save(
        copy_factory(
            book_id=book.id,
            inventory_number='INV-CARD-1',
            shelf=ShelfLocation(hall='Читальный зал', rack=2, shelf=5),
        ),
    )
    second = db_copies_repo.save(
        copy_factory(
            book_id=book.id,
            inventory_number='INV-CARD-2',
            shelf=ShelfLocation(hall='Абонемент', rack=1, shelf=3),
        ),
    )
    second.take()
    db_copies_repo.save(second)

    card = db_get_book_gateway.run(GetBookParams(id=book.id))

    assert card is not None
    assert card.id == book.id
    assert card.isbn == book.isbn
    assert card.title == book.title
    assert card.published_year == book.published_year
    assert card.authors == ['Лев Толстой', 'Второй автор']
    assert [copy.id for copy in card.copies] == [first.id, second.id]

    located = card.copies[0]
    assert located.inventory_number == 'INV-CARD-1'
    assert located.hall == 'Читальный зал'
    assert located.rack == 2
    assert located.shelf == 5
    assert located.is_available is True
    assert card.copies[1].is_available is False


def test_card_without_copies(
    db_get_book_gateway: GetBookGateway,
    db_books_repo: BooksRepo,
    book_factory: Callable[..., Book],
) -> None:
    book = db_books_repo.save(book_factory())
    assert book.id is not None

    card = db_get_book_gateway.run(GetBookParams(id=book.id))

    assert card is not None
    assert card.copies == []


def test_missing_book_returns_none(
    db_get_book_gateway: GetBookGateway,
) -> None:
    assert db_get_book_gateway.run(GetBookParams(id=987654)) is None
