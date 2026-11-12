from collections.abc import Callable
from datetime import date, timedelta
from uuid import uuid4

import pytest

from library.app.domain.book import Book, BooksRepo
from library.app.domain.copy import CopiesRepo, Copy
from library.app.domain.loan import (
    Extension,
    Loan,
    LoanPeriod,
    LoansRepo,
)
from library.app.domain.reader import Reader, ReadersRepo
from library.app.queries.loans.find_loans import (
    FindLoansGateway,
    FindLoansParams,
)

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)


@pytest.fixture
def seeded_loans(
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
    copies = [
        db_copies_repo.save(
            copy_factory(
                book_id=book.id,
                inventory_number=f'INV-{uuid4().hex}',
            ),
        )
        for _ in range(2)
    ]
    first_copy, second_copy = copies
    assert first_copy.id is not None
    assert second_copy.id is not None
    readers = [
        db_readers_repo.save(reader_factory()),
        db_readers_repo.save(reader_factory()),
    ]
    first_reader, second_reader = readers
    assert first_reader.id is not None
    assert second_reader.id is not None
    overdue_period = LoanPeriod(
        start=TODAY - timedelta(days=30),
        due=YESTERDAY,
    )
    active_period = LoanPeriod(
        start=TODAY,
        due=TODAY + timedelta(days=Loan.TERM_DAYS),
    )
    loans = [
        db_loans_repo.save(
            loan_factory(
                reader_id=first_reader.id,
                copy_id=first_copy.id,
                period=active_period,
                extensions=[
                    Extension(
                        extended_at=TOMORROW,
                        new_due=TODAY + timedelta(days=Loan.TERM_DAYS + 7),
                    ),
                ],
            ),
        ),
        db_loans_repo.save(
            loan_factory(
                reader_id=first_reader.id,
                copy_id=first_copy.id,
                period=overdue_period,
            ),
        ),
        db_loans_repo.save(
            loan_factory(
                reader_id=first_reader.id,
                copy_id=second_copy.id,
                period=overdue_period,
                returned_at=TODAY,
            ),
        ),
        db_loans_repo.save(
            loan_factory(
                reader_id=second_reader.id,
                copy_id=second_copy.id,
                period=active_period,
            ),
        ),
    ]
    return readers, loans


def _ids(loans: list[Loan]) -> list[int | None]:
    return [loan.id for loan in loans]


def test_returns_all_loans_ordered_by_id(
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
) -> None:
    _, loans = seeded_loans

    found = db_find_loans_gateway.run(FindLoansParams(), on=TODAY)

    assert [item.id for item in found] == _ids(loans)


def test_filters_by_reader(
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
) -> None:
    readers, loans = seeded_loans
    first_reader = readers[0]
    assert first_reader.id is not None

    found = db_find_loans_gateway.run(
        FindLoansParams(reader_id=first_reader.id),
        on=TODAY,
    )

    expected = [loan for loan in loans if loan.reader_id == first_reader.id]
    assert [item.id for item in found] == _ids(expected)


def test_filters_only_active(
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
) -> None:
    _, loans = seeded_loans

    found = db_find_loans_gateway.run(
        FindLoansParams(only_active=True),
        on=TODAY,
    )

    expected = [loan for loan in loans if loan.returned_at is None]
    assert [item.id for item in found] == _ids(expected)


def test_filters_only_overdue(
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
) -> None:
    _, loans = seeded_loans

    found = db_find_loans_gateway.run(
        FindLoansParams(only_overdue=True),
        on=TODAY,
    )

    expected = [
        loan for loan in loans if loan.returned_at is None and loan.period.due < TODAY
    ]
    assert [item.id for item in found] == _ids(expected)


def test_combines_reader_active_and_overdue(
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
) -> None:
    readers, loans = seeded_loans
    first_reader = readers[0]
    assert first_reader.id is not None

    found = db_find_loans_gateway.run(
        FindLoansParams(
            reader_id=first_reader.id,
            only_active=True,
            only_overdue=True,
        ),
        on=TODAY,
    )

    expected = [
        loan
        for loan in loans
        if loan.reader_id == first_reader.id
        and loan.returned_at is None
        and loan.period.due < TODAY
    ]
    assert [item.id for item in found] == _ids(expected)


def test_overdue_depends_on_request_date(
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
) -> None:
    _, loans = seeded_loans

    found = db_find_loans_gateway.run(
        FindLoansParams(only_overdue=True),
        on=TODAY + timedelta(days=Loan.TERM_DAYS + 1),
    )

    expected = [
        loan
        for loan in loans
        if loan.returned_at is None
        and loan.period.due < TODAY + timedelta(days=Loan.TERM_DAYS + 1)
    ]
    assert [item.id for item in found] == _ids(expected)


def test_maps_dto_fields(
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
) -> None:
    _, loans = seeded_loans
    with_extension, overdue, returned, _ = loans

    found = {
        item.id: item for item in db_find_loans_gateway.run(FindLoansParams(), on=TODAY)
    }

    assert with_extension.id is not None
    assert overdue.id is not None
    assert returned.id is not None
    item = found[with_extension.id]
    assert item.reader_id == with_extension.reader_id
    assert item.copy_id == with_extension.copy_id
    assert item.start == with_extension.period.start
    assert item.due == with_extension.period.due
    assert item.returned_at is None
    assert item.extensions_count == 1

    returned_item = found[returned.id]
    assert returned_item.returned_at == TODAY
    assert returned_item.extensions_count == 0


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
    db_find_loans_gateway: FindLoansGateway,
    seeded_loans: tuple[list[Reader], list[Loan]],
    limit: int,
    offset: int,
    expected_indexes: list[int],
) -> None:
    _, loans = seeded_loans

    found = db_find_loans_gateway.run(
        FindLoansParams(limit=limit, offset=offset),
        on=TODAY,
    )

    assert [item.id for item in found] == [
        loans[index].id for index in expected_indexes
    ]
