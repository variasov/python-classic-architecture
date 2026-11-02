import logging
from dataclasses import dataclass

from library.app.commands.domain.book import BooksRepo, ShelfLocation
from library.app.roles import Account, Permissions


@dataclass(frozen=True)
class AddCopyParams:
    book_id: int
    inventory_number: str
    hall: str
    rack: int
    shelf: int


class AddCopy:
    def __init__(self, books: BooksRepo, logger: logging.Logger) -> None:
        self.books = books
        self.logger = logger

    def run(self, params: AddCopyParams, account: Account) -> None:
        account.ensure(Permissions.BOOKS_EDIT)
        book = self.books.get_by_id(params.book_id)
        book.add_copy(
            params.inventory_number,
            ShelfLocation(hall=params.hall, rack=params.rack, shelf=params.shelf),
        )
        self.books.save(book)
        self.logger.info(
            'Добавлен экземпляр %s книги %s',
            params.inventory_number,
            params.book_id,
        )
