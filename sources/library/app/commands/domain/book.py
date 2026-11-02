from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import ClassVar

from classic.criteria import Criteria, criteria
from library.app.commands.domain.errors import DomainError


class InvalidIsbn(DomainError):
    def __str__(self) -> str:
        return 'ISBN должен состоять из 13 цифр'


class TitleEmpty(DomainError):
    def __str__(self) -> str:
        return 'Название книги не может быть пустым'


@dataclass
class PublishedInFuture(DomainError):
    published_year: int

    def __str__(self) -> str:
        return f'Год издания {self.published_year} ещё не наступил'


@dataclass
class DuplicateInventoryNumber(DomainError):
    inventory_number: str

    def __str__(self) -> str:
        return f'Инвентарный номер {self.inventory_number} уже есть в книге'


@dataclass
class ShelfPositionInvalid(DomainError):
    rack: int
    shelf: int

    def __str__(self) -> str:
        return f'Стеллаж {self.rack} и полка {self.shelf} должны быть не меньше 1'


@dataclass
class CopyNotFound(DomainError):
    inventory_number: str

    def __str__(self) -> str:
        return f'Экземпляр {self.inventory_number} не найден'


@dataclass
class CopyNotAvailable(DomainError):
    inventory_number: str

    def __str__(self) -> str:
        return f'Экземпляр {self.inventory_number} недоступен'


@dataclass
class CopyAlreadyAvailable(DomainError):
    inventory_number: str

    def __str__(self) -> str:
        return f'Экземпляр {self.inventory_number} уже на полке'


@dataclass
class BookNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Книга с id={self.id} не найдена'


@dataclass(frozen=True)
class ShelfLocation:
    """Объект-значение: место экземпляра на полке."""

    hall: str
    rack: int
    shelf: int

    def check(self) -> None:
        if self.rack < 1 or self.shelf < 1:
            raise ShelfPositionInvalid(rack=self.rack, shelf=self.shelf)


@dataclass
class Copy:
    """Вложенная сущность: экземпляр книги."""

    inventory_number: str
    shelf: ShelfLocation
    is_available: bool = True

    def check(self) -> None:
        self.shelf.check()


@dataclass
class Book:
    """Корень агрегата."""

    ISBN_LENGTH: ClassVar[int] = 13

    isbn: str
    title: str
    authors: list[str]
    published_year: int
    copies: list[Copy] = field(default_factory=list[Copy])
    id: int | None = None

    def check(self) -> None:
        if (
            len(self.isbn) != self.ISBN_LENGTH
            or not self.isbn.isascii()
            or not self.isbn.isdigit()
        ):
            raise InvalidIsbn
        if not self.title.strip():
            raise TitleEmpty
        numbers = [copy.inventory_number for copy in self.copies]
        for number in numbers:
            if numbers.count(number) > 1:
                raise DuplicateInventoryNumber(inventory_number=number)
        for copy in self.copies:
            copy.check()

    def check_published(self, on: date) -> None:
        """Год издания не позже года даты `on`. Дату передаёт вызывающий."""
        if self.published_year > on.year:
            raise PublishedInFuture(published_year=self.published_year)

    def add_copy(self, inventory_number: str, shelf: ShelfLocation) -> None:
        if any(c.inventory_number == inventory_number for c in self.copies):
            raise DuplicateInventoryNumber(inventory_number=inventory_number)
        copy = Copy(inventory_number=inventory_number, shelf=shelf)
        copy.check()
        self.copies.append(copy)

    def take_copy(self, inventory_number: str) -> None:
        copy = self._get_copy(inventory_number)
        if not copy.is_available:
            raise CopyNotAvailable(inventory_number=inventory_number)
        copy.is_available = False

    def return_copy(self, inventory_number: str) -> None:
        copy = self._get_copy(inventory_number)
        if copy.is_available:
            raise CopyAlreadyAvailable(inventory_number=inventory_number)
        copy.is_available = True

    def _get_copy(self, inventory_number: str) -> Copy:
        for copy in self.copies:
            if copy.inventory_number == inventory_number:
                return copy
        raise CopyNotFound(inventory_number=inventory_number)

    @criteria
    def has_available_copies(self) -> bool:
        return any(copy.is_available for copy in self.copies)

    @criteria
    def published_after(self, year: int) -> bool:
        return self.published_year > year

    @criteria
    def written_by(self, author: str) -> bool:
        return author in self.authors


class BooksRepo(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Book: ...

    @abstractmethod
    def save(self, book: Book) -> Book: ...

    @abstractmethod
    def find(self, criteria: Criteria[Book]) -> list[Book]: ...
