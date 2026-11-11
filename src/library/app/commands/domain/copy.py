from abc import ABC, abstractmethod
from dataclasses import dataclass

from classic.criteria import Criteria, criteria

from library.app.commands.domain.errors import DomainError


class InventoryNumberEmpty(DomainError):
    def __str__(self) -> str:
        return 'Инвентарный номер не может быть пустым'


@dataclass
class ShelfLocationInvalid(DomainError):
    rack: int
    shelf: int

    def __str__(self) -> str:
        return f'Место на полке задано неверно: стеллаж={self.rack}, полка={self.shelf}'


@dataclass
class CopyNotAvailable(DomainError):
    copy_id: int | None

    def __str__(self) -> str:
        return f'Экземпляр с id={self.copy_id} уже выдан'


@dataclass
class CopyNotTaken(DomainError):
    copy_id: int | None

    def __str__(self) -> str:
        return f'Экземпляр с id={self.copy_id} не выдан'


@dataclass
class CopyNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Экземпляр с id={self.id} не найден'


@dataclass(frozen=True)
class ShelfLocation:
    """Объект-значение: место хранения экземпляра."""

    hall: str
    rack: int
    shelf: int

    def check(self) -> None:
        if self.rack < 1 or self.shelf < 1:
            raise ShelfLocationInvalid(rack=self.rack, shelf=self.shelf)


@dataclass
class Copy:
    """Корень агрегата: экземпляр книги."""

    book_id: int
    inventory_number: str
    shelf: ShelfLocation
    is_available: bool = True
    id: int | None = None

    def check(self) -> None:
        if not self.inventory_number.strip():
            raise InventoryNumberEmpty
        self.shelf.check()

    def take(self) -> None:
        if not self.is_available:
            raise CopyNotAvailable(copy_id=self.id)
        self.is_available = False

    def give_back(self) -> None:
        if self.is_available:
            raise CopyNotTaken(copy_id=self.id)
        self.is_available = True

    @criteria
    def available(self) -> bool:
        return self.is_available

    @criteria
    def of_book(self, book_id: int) -> bool:
        return self.book_id == book_id

    @criteria
    def with_inventory_number(self, inventory_number: str) -> bool:
        return self.inventory_number == inventory_number


class CopiesRepo(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Copy: ...

    @abstractmethod
    def save(self, copy: Copy) -> Copy: ...

    @abstractmethod
    def find(self, criteria: Criteria[Copy]) -> list[Copy]: ...
