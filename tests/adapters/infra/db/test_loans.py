from datetime import date

import pytest

from library.app.commands.domain.loan import (
    Extension,
    Loan,
    LoanNotFound,
    LoanPeriod,
    TooManyExtensions,
)


def test_loans_repo_roundtrip(any_loans_repo, loan_factory_with_parents) -> None:
    loan = loan_factory_with_parents()
    loan.extend(on=date(2026, 3, 10), days=7)
    saved = any_loans_repo.save(loan)
    loaded = any_loans_repo.get_by_id(saved.id)
    assert loaded == saved


def test_loans_repo_update_extensions(
    any_loans_repo,
    loan_factory_with_parents,
) -> None:
    loan = loan_factory_with_parents()
    loan.extend(on=date(2026, 3, 10), days=7)
    saved = any_loans_repo.save(loan)
    loaded = any_loans_repo.get_by_id(saved.id)
    loaded.extend(on=date(2026, 3, 10), days=7)
    any_loans_repo.save(loaded)
    with_two = any_loans_repo.get_by_id(saved.id)
    assert len(with_two.extensions) == 2

    with_two.extensions = [with_two.extensions[0]]
    with_two.period = LoanPeriod(
        start=with_two.period.start,
        due=with_two.extensions[0].new_due,
    )
    any_loans_repo.save(with_two)
    with_one = any_loans_repo.get_by_id(saved.id)
    assert len(with_one.extensions) == 1


def test_loans_repo_close(any_loans_repo, loan_factory_with_parents) -> None:
    saved = any_loans_repo.save(loan_factory_with_parents())
    loaded = any_loans_repo.get_by_id(saved.id)
    loaded.close(on=date(2026, 3, 15))
    any_loans_repo.save(loaded)
    assert any_loans_repo.get_by_id(saved.id).returned_at == date(
        2026,
        3,
        15,
    )


def test_loans_repo_not_found(any_loans_repo) -> None:
    with pytest.raises(LoanNotFound):
        any_loans_repo.get_by_id(999999)


def test_loans_repo_invalid_is_not_saved(
    db_loans_repo,
    raw_db,
    loan_factory,
) -> None:
    loan = loan_factory()
    loan.extensions = [
        Extension(extended_at=date(2026, 3, 10), new_due=date(2026, 3, 17)),
        Extension(extended_at=date(2026, 3, 10), new_due=date(2026, 3, 24)),
        Extension(extended_at=date(2026, 3, 10), new_due=date(2026, 3, 31)),
    ]
    loan.period = LoanPeriod(
        start=date(2026, 3, 10),
        due=date(2026, 3, 31),
    )
    before = raw_db.scalar('SELECT count(*) FROM library.loans')
    with pytest.raises(TooManyExtensions):
        db_loans_repo.save(loan)
    after = raw_db.scalar('SELECT count(*) FROM library.loans')
    assert after == before


def _saved_loans(repo, loan_factory_with_parents) -> list[Loan]:
    overdue = loan_factory_with_parents(
        reader_id=1,
        period=LoanPeriod(
            start=date(2026, 2, 1),
            due=date(2026, 2, 15),
        ),
    )
    returned = loan_factory_with_parents(
        reader_id=1,
        issued_at=date(2026, 2, 1),
        returned_at=date(2026, 2, 10),
        period=LoanPeriod(
            start=date(2026, 2, 1),
            due=date(2026, 2, 15),
        ),
    )
    actual = loan_factory_with_parents(
        reader_id=2,
        period=LoanPeriod(
            start=date(2026, 3, 10),
            due=date(2026, 3, 24),
        ),
    )
    return [
        repo.save(overdue),
        repo.save(returned),
        repo.save(actual),
    ]


@pytest.mark.parametrize(
    'criteria_name',
    [
        'overdue',
        'returned',
        'due_within',
        'reader',
        'combination',
    ],
)
def test_loans_repo_find_by_criteria(
    any_loans_repo,
    loan_factory_with_parents,
    criteria_name: str,
) -> None:
    loans = _saved_loans(any_loans_repo, loan_factory_with_parents)
    criteria = {
        'overdue': Loan.overdue(on=date(2026, 3, 10)),
        'returned': Loan.returned(),
        'due_within': Loan.due_within(on=date(2026, 3, 10), days=20),
        'reader': Loan.belongs_to_reader(reader_id=1),
        'combination': (
            Loan.belongs_to_reader(reader_id=1) & ~Loan.returned()
        ),
    }[criteria_name]
    expected = {
        loan.id for loan in loans if criteria.is_satisfied_by(loan)
    }
    actual = {loan.id for loan in any_loans_repo.find(criteria)}
    assert actual == expected


