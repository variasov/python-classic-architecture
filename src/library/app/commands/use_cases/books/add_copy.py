import logging
from dataclasses import dataclass
from typing import ClassVar

from library.app.commands.domain.book import BooksRepo
from library.app.commands.domain.copy import CopiesRepo, Copy, ShelfLocation
from library.app.errors import AppError
from library.app.roles import Account, Permissions


@dataclass
class InventoryNumberTaken(AppError):
    inventory_number: str

    def __str__(self) -> str:
        return f'Инвентарный номер {self.inventory_number} уже занят'


@dataclass(frozen=True)
class AddCopyParams:
    """Параметры добавления экземпляра."""

    book_id: int
    inventory_number: str
    hall: str
    rack: int
    shelf: int

    MIN_POSITION: ClassVar[int] = 1

    def __post_init__(self) -> None:
        if self.rack < self.MIN_POSITION:
            raise ValueError(
                f'Стеллаж должен быть не меньше {self.MIN_POSITION}',
            )
        if self.shelf < self.MIN_POSITION:
            raise ValueError(f'Полка должна быть не меньше {self.MIN_POSITION}')


class AddCopy:
    """Добавление экземпляра книги."""

    def __init__(
        self,
        books: BooksRepo,
        copies: CopiesRepo,
        logger: logging.Logger,
    ) -> None:
        self._books = books
        self._copies = copies
        self._logger = logger

    def run(self, params: AddCopyParams, account: Account) -> int:
        account.require(Permissions.BOOKS_EDIT)
        self._books.get_by_id(params.book_id)
        taken = self._copies.find(
            Copy.with_inventory_number(inventory_number=params.inventory_number),
        )
        if taken:
            raise InventoryNumberTaken(inventory_number=params.inventory_number)
        copy = Copy(
            book_id=params.book_id,
            inventory_number=params.inventory_number,
            shelf=ShelfLocation(
                hall=params.hall,
                rack=params.rack,
                shelf=params.shelf,
            ),
        )
        saved = self._copies.save(copy)
        assert saved.id is not None
        self._logger.info('Экземпляр добавлен: id=%s', saved.id)
        return saved.id
