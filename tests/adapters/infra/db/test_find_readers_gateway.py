from collections.abc import Callable
from datetime import date, timedelta
from uuid import uuid4

import pytest

from library.app.commands.domain.book import Book, BooksRepo
from library.app.commands.domain.copy import CopiesRepo, Copy
from library.app.commands.domain.loan import (
    Loan,
    LoanPeriod,
    LoansRepo,
)
from library.app.commands.domain.reader import (
    Contact,
    Reader,
    ReadersRepo,
)
from library.app.queries.readers.find_readers import (
    FindReadersGateway,
    FindReadersParams,
)

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)


@pytest.fixture
def seeded_readers(
    db_books_repo: BooksRepo,
    db_copies_repo: CopiesRepo,
    db_readers_repo: ReadersRepo,
    db_loans_repo: LoansRepo,
    book_factory: Callable[..., Book],
    copy_factory: Callable[..., Copy],
    reader_factory: Callable[..., Reader],
    loan_factory: Callable[..., Loan],
) -> tuple[list[Reader], list[Loan]]:
    book = db_books_repo.save(book_factory())
    assert book.id is not None
    copy = db_copies_repo.save(
        copy_factory(book_id=book.id, inventory_number=f'INV-{uuid4().hex}'),
    )
    assert copy.id is not None
    readers = [
        db_readers_repo.save(
            reader_factory(
                full_name='Первый читатель',
                contact=Contact(email=f'first-{uuid4().hex}@example.com'),
            ),
        ),
        db_readers_repo.save(
            reader_factory(
                full_name='Второй читатель',
                contact=Contact(email=f'second-{uuid4().hex}@example.com'),
            ),
        ),
        db_readers_repo.save(
            reader_factory(
                full_name='Третий читатель',
                contact=Contact(email=f'third-{uuid4().hex}@example.com'),
            ),
        ),
    ]
    first = readers[0]
    third = readers[2]
    assert first.id is not None
    assert third.id is not None
    loans = [
        db_loans_repo.save(
            loan_factory(
                reader_id=first.id,
                copy_id=copy.id,
                period=LoanPeriod(
                    start=TODAY - timedelta(days=30),
                    due=YESTERDAY,
                ),
            ),
        ),
        db_loans_repo.save(
            loan_factory(
                reader_id=first.id,
                copy_id=copy.id,
                period=LoanPeriod(
                    start=TODAY - timedelta(days=5),
                    due=TODAY + timedelta(days=5),
                ),
            ),
        ),
        db_loans_repo.save(
            loan_factory(
                reader_id=first.id,
                copy_id=copy.id,
                period=LoanPeriod(
                    start=TODAY - timedelta(days=30),
                    due=YESTERDAY,
                ),
                returned_at=TODAY,
            ),
        ),
        db_loans_repo.save(
            loan_factory(
                reader_id=third.id,
                copy_id=copy.id,
                period=LoanPeriod(
                    start=TODAY - timedelta(days=30),
                    due=YESTERDAY,
                ),
                returned_at=TOMORROW,
            ),
        ),
    ]
    return readers, loans


def _by_id(
    readers: list[Reader],
) -> dict[int, Reader]:
    return {reader.id: reader for reader in readers if reader.id is not None}


def test_counts_active_and_overdue_loans(
    db_find_readers_gateway: FindReadersGateway,
    seeded_readers: tuple[list[Reader], list[Loan]],
) -> None:
    readers, _ = seeded_readers

    found = db_find_readers_gateway.run(FindReadersParams(), on=TODAY)

    assert [item.id for item in found] == [reader.id for reader in readers]
    counts = {item.id: (item.active_loans, item.overdue_loans) for item in found}
    first, second, third = readers
    assert first.id is not None
    assert second.id is not None
    assert third.id is not None
    assert counts[first.id] == (2, 1)
    assert counts[second.id] == (0, 0)
    assert counts[third.id] == (0, 0)


def test_maps_reader_fields(
    db_find_readers_gateway: FindReadersGateway,
    seeded_readers: tuple[list[Reader], list[Loan]],
) -> None:
    readers, _ = seeded_readers

    found = db_find_readers_gateway.run(FindReadersParams(), on=TODAY)

    by_id = _by_id(readers)
    for item in found:
        reader = by_id[item.id]
        assert item.full_name == reader.full_name
        assert item.email == reader.contact.email


def test_overdue_depends_on_request_date(
    db_find_readers_gateway: FindReadersGateway,
    seeded_readers: tuple[list[Reader], list[Loan]],
) -> None:
    readers, _ = seeded_readers
    first = readers[0]
    assert first.id is not None

    found = db_find_readers_gateway.run(
        FindReadersParams(),
        on=TODAY + timedelta(days=10),
    )

    counts = {item.id: (item.active_loans, item.overdue_loans) for item in found}
    assert counts[first.id] == (2, 2)


@pytest.mark.parametrize(
    ('limit', 'offset', 'expected_indexes'),
    [
        (1, 0, [0]),
        (1, 1, [1]),
        (2, 1, [1, 2]),
        (10, 10, []),
    ],
)
def test_paginates(
    db_find_readers_gateway: FindReadersGateway,
    seeded_readers: tuple[list[Reader], list[Loan]],
    limit: int,
    offset: int,
    expected_indexes: list[int],
) -> None:
    readers, _ = seeded_readers

    found = db_find_readers_gateway.run(
        FindReadersParams(limit=limit, offset=offset),
        on=TODAY,
    )

    assert [item.id for item in found] == [
        readers[index].id for index in expected_indexes
    ]
