from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

from classic.criteria import Criteria, criteria

from library.app.commands.domain.errors import DomainError


class IsbnInvalid(DomainError):
    def __init__(self, isbn: str) -> None:
        self.isbn = isbn

    def __str__(self) -> str:
        return f'ISBN {self.isbn!r} должен состоять из 13 цифр'


class BookTitleEmpty(DomainError):
    def __str__(self) -> str:
        return 'Название книги не может быть пустым'


@dataclass
class PublishedYearInFuture(DomainError):
    year: int
    current_year: int

    def __str__(self) -> str:
        return f'Год издания {self.year} больше текущего года {self.current_year}'


@dataclass
class ShelfRackInvalid(DomainError):
    rack: int

    def __str__(self) -> str:
        return f'Номер стеллажа должен быть не меньше 1, получен {self.rack}'


@dataclass
class ShelfShelfInvalid(DomainError):
    shelf: int

    def __str__(self) -> str:
        return f'Номер полки должен быть не меньше 1, получен {self.shelf}'


@dataclass
class DuplicateInventoryNumber(DomainError):
    inventory_number: str

    def __str__(self) -> str:
        return f'Инвентарный номер {self.inventory_number!r} повторяется'


@dataclass
class CopyNotFound(DomainError):
    book_id: int | None
    inventory_number: str

    def __str__(self) -> str:
        return (
            f'Экземпляр {self.inventory_number!r} не найден в книге с id={self.book_id}'
        )


@dataclass
class CopyNotAvailable(DomainError):
    book_id: int | None
    inventory_number: str

    def __str__(self) -> str:
        return (
            f'Экземпляр {self.inventory_number!r} книги с id={self.book_id} уже выдан'
        )


@dataclass
class BookNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Книга с id={self.id} не найдена'


@dataclass
class NoAvailableCopies(DomainError):
    book_id: int

    def __str__(self) -> str:
        return f'У книги с id={self.book_id} нет доступных экземпляров'


@dataclass
class BookNotInCatalog(DomainError):
    isbn: str

    def __str__(self) -> str:
        return f'Книга с ISBN {self.isbn!r} не найдена в каталоге'


@dataclass(frozen=True)
class ShelfLocation:
    hall: str
    rack: int
    shelf: int

    def check(self) -> None:
        if self.rack < 1:
            raise ShelfRackInvalid(rack=self.rack)
        if self.shelf < 1:
            raise ShelfShelfInvalid(shelf=self.shelf)


@dataclass
class Copy:
    inventory_number: str
    shelf: ShelfLocation
    is_available: bool = True

    def check(self) -> None:
        self.shelf.check()


@dataclass
class Book:
    isbn: str
    title: str
    authors: list[str]
    published_year: int
    copies: list[Copy] = field(default_factory=list[Copy])
    id: int | None = None

    ISBN_LENGTH: ClassVar[int] = 13

    def check(self, current_year: int | None = None) -> None:
        if len(self.isbn) != self.ISBN_LENGTH or not self.isbn.isdigit():
            raise IsbnInvalid(isbn=self.isbn)
        if not self.title.strip():
            raise BookTitleEmpty
        if current_year is not None and self.published_year > current_year:
            raise PublishedYearInFuture(
                year=self.published_year,
                current_year=current_year,
            )
        seen: set[str] = set()
        for copy in self.copies:
            if copy.inventory_number in seen:
                raise DuplicateInventoryNumber(
                    inventory_number=copy.inventory_number,
                )
            seen.add(copy.inventory_number)
            copy.check()

    def add_copy(self, inventory_number: str, shelf: ShelfLocation) -> None:
        self.copies.append(
            Copy(inventory_number=inventory_number, shelf=shelf),
        )

    def take_copy(self, inventory_number: str) -> None:
        copy = self._find_copy(inventory_number)
        if not copy.is_available:
            raise CopyNotAvailable(
                book_id=self.id,
                inventory_number=inventory_number,
            )
        copy.is_available = False

    def return_copy(self, inventory_number: str) -> None:
        self._find_copy(inventory_number).is_available = True

    def _find_copy(self, inventory_number: str) -> Copy:
        for copy in self.copies:
            if copy.inventory_number == inventory_number:
                return copy
        raise CopyNotFound(
            book_id=self.id,
            inventory_number=inventory_number,
        )

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
