from collections.abc import Callable, Iterator
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

import pytest
from classic.criteria import Criteria, ReturnsTrue

from library.app.commands.domain.book import Book
from library.app.commands.domain.copy import Copy
from library.app.commands.domain.loan import (
    Extension,
    Loan,
    LoanNotFound,
    LoanPeriod,
    LoanPeriodInvalid,
    LoansRepo,
    TooManyExtensions,
)
from library.app.commands.domain.reader import Reader
from library.infra.db.repos.books import DbBooksRepo
from library.infra.db.repos.copies import DbCopiesRepo
from library.infra.db.repos.loans import DbLoansRepo
from library.infra.db.repos.readers import DbReadersRepo

TODAY = date(2026, 3, 10)
TOMORROW = date(2026, 3, 11)
YESTERDAY = date(2026, 3, 9)
IN_A_WEEK = TODAY + timedelta(days=7)
IN_A_MONTH = TODAY + timedelta(days=30)


@pytest.fixture(params=['db', 'in_memory'])
def loans_env(
    request: pytest.FixtureRequest,
    db_engine: Any,
    raw_db: Any,
    reader_factory: Callable[..., Reader],
    book_factory: Callable[..., Book],
    copy_factory: Callable[..., Copy],
) -> Iterator[tuple[LoansRepo, tuple[int, int], tuple[int, int]]]:
    """Репозиторий выдач, id двух читателей и id двух экземпляров"""
    if request.param == 'db':
        readers = DbReadersRepo(db_engine)
        books = DbBooksRepo(db_engine)
        copies = DbCopiesRepo(db_engine)
        reader = readers.save(reader_factory())
        other_reader = readers.save(reader_factory())
        book = books.save(book_factory())
        assert reader.id is not None
        assert other_reader.id is not None
        assert book.id is not None
        copy = copies.save(
            copy_factory(
                book_id=book.id, inventory_number=f'INV-{uuid4().hex}'
            )
        )
        other_copy = copies.save(
            copy_factory(
                book_id=book.id, inventory_number=f'INV-{uuid4().hex}'
            )
        )
        assert copy.id is not None
        assert other_copy.id is not None
        yield (
            DbLoansRepo(db_engine),
            (reader.id, other_reader.id),
            (copy.id, other_copy.id),
        )
        raw_db.execute(
            'DELETE FROM library.readers WHERE id = %(id)s', id=reader.id
        )
        raw_db.execute(
            'DELETE FROM library.readers WHERE id = %(id)s', id=other_reader.id
        )
        raw_db.execute(
            'DELETE FROM library.books WHERE id = %(id)s', id=book.id
        )
        return
    in_memory: LoansRepo = request.getfixturevalue('in_memory_loans_repo')
    yield in_memory, (1, 2), (1, 2)


def _load(repo: LoansRepo, loan: Loan) -> Loan:
    assert loan.id is not None
    return repo.get_by_id(loan.id)


def test_saved_loan_is_read_back(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    loan_factory: Callable[..., Loan],
) -> None:
    repo, (reader_id, _), (copy_id, _) = loans_env
    loan = repo.save(
        loan_factory(reader_id=reader_id, copy_id=copy_id)
    )

    loaded = _load(repo, loan)

    assert loaded == loan
    assert loaded.period == LoanPeriod(TODAY, TODAY + timedelta(days=14))
    assert loaded.extensions == []


def test_extensions_are_read_back_in_order(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    loan_factory: Callable[..., Loan],
) -> None:
    repo, (reader_id, _), (copy_id, _) = loans_env
    extensions = [
        Extension(extended_at=TOMORROW, new_due=TODAY + timedelta(days=21)),
        Extension(
            extended_at=TODAY + timedelta(days=21),
            new_due=TODAY + timedelta(days=28),
        ),
    ]
    loan = repo.save(
        loan_factory(
            reader_id=reader_id,
            copy_id=copy_id,
            extensions=extensions,
        )
    )

    loaded = _load(repo, loan)

    assert loaded.extensions == extensions


def test_update_rewrites_fields_and_extensions(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    loan_factory: Callable[..., Loan],
) -> None:
    repo, (reader_id, _), (copy_id, _) = loans_env
    loan = repo.save(
        loan_factory(reader_id=reader_id, copy_id=copy_id)
    )
    loan.period = LoanPeriod(start=TODAY, due=TODAY + timedelta(days=20))
    loan.returned_at = TOMORROW
    loan.extensions = [
        Extension(extended_at=TOMORROW, new_due=TODAY + timedelta(days=21)),
        Extension(
            extended_at=TODAY + timedelta(days=21),
            new_due=TODAY + timedelta(days=28),
        ),
    ]

    repo.save(loan)
    loaded = _load(repo, loan)

    assert loaded == loan
    assert loaded.returned_at == TOMORROW
    assert len(loaded.extensions) == 2


def test_extensions_can_be_removed(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    loan_factory: Callable[..., Loan],
) -> None:
    repo, (reader_id, _), (copy_id, _) = loans_env
    loan = repo.save(
        loan_factory(
            reader_id=reader_id,
            copy_id=copy_id,
            extensions=[
                Extension(
                    extended_at=TOMORROW, new_due=TODAY + timedelta(days=21)
                )
            ],
        )
    )
    loan.extensions = []

    repo.save(loan)

    assert _load(repo, loan).extensions == []


def test_get_missing_loan_raises(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
) -> None:
    repo, _, _ = loans_env

    with pytest.raises(LoanNotFound):
        repo.get_by_id(987654)


def test_save_loan_with_too_many_extensions_writes_nothing(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    loan_factory: Callable[..., Loan],
) -> None:
    repo, (reader_id, _), (copy_id, _) = loans_env
    loan = loan_factory(
        reader_id=reader_id,
        copy_id=copy_id,
        extensions=[
            Extension(extended_at=TOMORROW, new_due=TODAY + timedelta(days=15)),
            Extension(
                extended_at=TODAY + timedelta(days=15),
                new_due=TODAY + timedelta(days=16),
            ),
            Extension(
                extended_at=TODAY + timedelta(days=16),
                new_due=TODAY + timedelta(days=17),
            ),
        ],
    )

    with pytest.raises(TooManyExtensions):
        repo.save(loan)

    assert repo.find(Loan.of_reader(reader_id=reader_id)) == []


def test_save_loan_with_invalid_period_writes_nothing(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    loan_factory: Callable[..., Loan],
) -> None:
    repo, (reader_id, _), (copy_id, _) = loans_env
    loan = loan_factory(
        reader_id=reader_id,
        copy_id=copy_id,
        period=LoanPeriod(start=TODAY, due=TODAY),
    )

    with pytest.raises(LoanPeriodInvalid):
        repo.save(loan)

    assert repo.find(Loan.of_reader(reader_id=reader_id)) == []


@pytest.fixture
def seeded_loans(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    loan_factory: Callable[..., Loan],
) -> list[Loan]:
    repo, (reader_id, other_reader_id), (copy_id, other_copy_id) = loans_env
    period = LoanPeriod(start=TODAY - timedelta(days=30), due=YESTERDAY)
    return [
        repo.save(
            loan_factory(reader_id=reader_id, copy_id=copy_id, period=period)
        ),
        repo.save(
            loan_factory(
                reader_id=reader_id,
                copy_id=copy_id,
                period=period,
                returned_at=YESTERDAY,
            )
        ),
        repo.save(
            loan_factory(
                reader_id=reader_id,
                copy_id=copy_id,
                period=LoanPeriod(start=TODAY - timedelta(days=14), due=TODAY),
            )
        ),
        repo.save(
            loan_factory(
                reader_id=reader_id,
                copy_id=other_copy_id,
                period=LoanPeriod(
                    start=TODAY - timedelta(days=14), due=IN_A_WEEK
                ),
            )
        ),
        repo.save(
            loan_factory(
                reader_id=reader_id,
                copy_id=other_copy_id,
                period=LoanPeriod(
                    start=TODAY - timedelta(days=14), due=IN_A_MONTH
                ),
                extensions=[
                    Extension(
                        extended_at=TOMORROW,
                        new_due=IN_A_MONTH + timedelta(days=7),
                    )
                ],
            )
        ),
        repo.save(
            loan_factory(
                reader_id=other_reader_id,
                copy_id=copy_id,
                period=period,
            )
        ),
    ]


def _criteria_map(
    reader_id: int, other_reader_id: int
) -> dict[str, Criteria[Loan]]:
    return {
        'overdue': Loan.overdue(on=TODAY),
        'returned': Loan.returned(),
        'due_within': Loan.due_within(on=TODAY, days=7),
        'of_reader': Loan.of_reader(reader_id=reader_id),
        'other_reader': Loan.of_reader(reader_id=other_reader_id),
        'overdue_and_of_reader': Loan.overdue(on=TODAY)
        & Loan.of_reader(reader_id=reader_id),
        'due_within_or_returned': Loan.due_within(on=TODAY, days=7)
        | Loan.returned(),
        'not_returned_and_of_reader': ~Loan.returned()
        & Loan.of_reader(reader_id=reader_id),
        'not_of_reader': ~Loan.of_reader(reader_id=reader_id),
    }


@pytest.mark.parametrize(
    'criteria_name',
    [
        'overdue',
        'returned',
        'due_within',
        'of_reader',
        'other_reader',
        'overdue_and_of_reader',
        'due_within_or_returned',
        'not_returned_and_of_reader',
        'not_of_reader',
    ],
)
def test_criteria_sql_matches_domain(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    seeded_loans: list[Loan],
    criteria_name: str,
) -> None:
    repo, (reader_id, other_reader_id), _ = loans_env
    criteria = _criteria_map(reader_id, other_reader_id)[criteria_name]

    found = repo.find(criteria)
    expected = [loan for loan in seeded_loans if criteria.is_satisfied_by(loan)]

    assert [loan.id for loan in found] == [loan.id for loan in expected]


def test_find_returns_whole_loans_with_extensions(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    seeded_loans: list[Loan],
) -> None:
    repo, (reader_id, _), _ = loans_env

    found = repo.find(Loan.of_reader(reader_id=reader_id))
    expected = [
        loan for loan in seeded_loans if loan.reader_id == reader_id
    ]

    assert found == expected
    assert len(found[-1].extensions) == 1


def test_find_returns_all_without_filters(
    loans_env: tuple[LoansRepo, tuple[int, int], tuple[int, int]],
    seeded_loans: list[Loan],
) -> None:
    repo, _, _ = loans_env

    assert len(repo.find(ReturnsTrue())) == len(seeded_loans)
