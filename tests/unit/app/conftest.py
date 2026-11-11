from collections.abc import Callable

import pytest

from library.app.commands.use_cases.books.create_book import CreateBookParams
from library.app.roles import Account, Permissions


@pytest.fixture
def admin() -> Account:
    return Account(
        login='admin',
        permissions=(Permissions.BOOKS_EDIT, Permissions.READERS_EDIT),
    )


@pytest.fixture
def no_books_permission() -> Account:
    return Account(login='guest', permissions=(Permissions.READERS_EDIT,))


@pytest.fixture
def create_book_params() -> Callable[..., CreateBookParams]:
    def factory(**overrides: object) -> CreateBookParams:
        fields: dict[str, object] = {
            'isbn': '9785171183660',
            'title': 'Война и мир',
            'authors': ['Лев Толстой'],
            'published_year': 1869,
        }
        fields.update(overrides)
        return CreateBookParams(**fields)  # type: ignore[arg-type]

    return factory
