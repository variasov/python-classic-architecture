from collections.abc import Callable
from datetime import timedelta

import pytest
from library.app.commands.domain.book import Book
from library.app.commands.domain.loan import (
    Extension,
    Loan,
    LoanNotFound,
    LoanPeriod,
    LoanPeriodInvalid,
    LoansRepo,
)
from library.app.commands.domain.reader import Reader
from library.infra.db.repos.loans_repo import DbLoansRepo

from tests.conftest import TODAY, RawDb


@pytest.fixture(params=['db_loans_repo', 'in_memory_loans_repo'])
def any_loans_repo(request: pytest.FixtureRequest) -> LoansRepo:
    return request.getfixturevalue(request.param)


def test_save_and_get_with_extensions(
    db_loans_repo: DbLoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(due_in_days=5)
    assert loan.id is not None
    loan.extend(on=TODAY, days=3)
    loan.extend(on=TODAY, days=4)
    db_loans_repo.save(loan)
    assert db_loans_repo.get_by_id(loan.id) == loan


def test_update_removes_extensions(
    db_loans_repo: DbLoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory(due_in_days=5)
    assert loan.id is not None
    loan.extend(on=TODAY, days=3)
    db_loans_repo.save(loan)
    loan.extensions.clear()
    db_loans_repo.save(loan)
    assert db_loans_repo.get_by_id(loan.id).extensions == []


def test_close_roundtrip(
    db_loans_repo: DbLoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory()
    assert loan.id is not None
    loan.close(TODAY)
    db_loans_repo.save(loan)
    assert db_loans_repo.get_by_id(loan.id).returned_at == TODAY


def test_not_found(any_loans_repo: LoansRepo) -> None:
    with pytest.raises(LoanNotFound):
        any_loans_repo.get_by_id(-1)


def test_save_unknown_id(
    db_loans_repo: DbLoansRepo,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory()
    loan.id = -3
    with pytest.raises(LoanNotFound):
        db_loans_repo.save(loan)


def test_save_invalid_writes_nothing(
    db_loans_repo: DbLoansRepo,
    loan_factory: Callable[..., Loan],
    raw_db: RawDb,
    marker: str,
) -> None:
    good = loan_factory()
    bad = Loan(
        reader_id=good.reader_id,
        book_id=good.book_id,
        inventory_number=f'{marker}-bad',
        issued_at=TODAY,
        period=LoanPeriod(start=TODAY, due=TODAY),
    )
    with pytest.raises(LoanPeriodInvalid):
        db_loans_repo.save(bad)
    count = raw_db.scalar(
        'SELECT count(*) FROM library.loans WHERE inventory_number = %(n)s',
        n=f'{marker}-bad',
    )
    assert count == 0


def test_find_by_criteria_matches_domain(
    any_loans_repo: LoansRepo,
    in_memory_loans_repo: LoansRepo,
    db_loans_repo: DbLoansRepo,
    reader_factory: Callable[..., Reader],
    book_factory: Callable[..., Book],
) -> None:
    reader, other = reader_factory(), reader_factory()
    book = book_factory(copies=1)
    loans: list[Loan] = []
    for owner, due_in_days, returned in [
        (reader, -3, False),
        (reader, 0, False),
        (reader, 10, False),
        (other, -5, True),
        (other, 2, False),
    ]:
        start = TODAY - timedelta(days=30)
        loan = Loan(
            reader_id=owner.id or 0,
            book_id=book.id or 0,
            inventory_number='X',
            issued_at=start,
            period=LoanPeriod(start=start, due=TODAY + timedelta(days=due_in_days)),
            returned_at=TODAY - timedelta(days=1) if returned else None,
        )
        loans.append(any_loans_repo.save(loan))
    ids = {x.id for x in loans}
    reader_id = reader.id or 0
    cases = [
        Loan.overdue(on=TODAY),
        Loan.returned(),
        Loan.due_within(on=TODAY, days=2),
        Loan.of_reader(reader_id=reader_id),
        ~Loan.returned() & Loan.of_reader(reader_id=reader_id),
        Loan.overdue(on=TODAY) | Loan.returned(),
    ]
    for criteria in cases:
        found = {x.id for x in any_loans_repo.find(criteria) if x.id in ids}
        assert found == {x.id for x in loans if criteria.is_satisfied_by(x)}
    assert db_loans_repo is not None
    assert in_memory_loans_repo is not None


def test_extension_value() -> None:
    assert Extension(extended_at=TODAY, new_due=TODAY + timedelta(days=1)) == Extension(
        extended_at=TODAY,
        new_due=TODAY + timedelta(days=1),
    )
