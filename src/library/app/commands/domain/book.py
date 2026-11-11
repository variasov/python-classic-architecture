from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from classic.criteria import Criteria, criteria

from library.app.commands.domain.errors import DomainError


class BookTitleEmpty(DomainError):
    def __str__(self) -> str:
        return 'Название книги не может быть пустым'


@dataclass
class BookIsbnInvalid(DomainError):
    isbn: str

    def __str__(self) -> str:
        return f'ISBN должен состоять из 13 цифр, получено: {self.isbn}'


@dataclass
class BookPublishedInFuture(DomainError):
    year: int

    def __str__(self) -> str:
        return f'Год издания {self.year} больше текущего года'


@dataclass
class BookNotFound(DomainError):
    id: int

    def __str__(self) -> str:
        return f'Книга с id={self.id} не найдена'


@dataclass
class Book:
    """Корень агрегата: книга"""

    isbn: str
    title: str
    authors: list[str]
    published_year: int
    id: int | None = None

    def check(self) -> None:
        if len(self.isbn) != 13 or not self.isbn.isdigit():
            raise BookIsbnInvalid(isbn=self.isbn)
        if not self.title.strip():
            raise BookTitleEmpty()
        if self.published_year > date.today().year:
            raise BookPublishedInFuture(year=self.published_year)

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
