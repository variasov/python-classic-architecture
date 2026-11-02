import logging
from collections.abc import Callable
from datetime import date, timedelta

import pytest
from classic.signals import Hub
from library.app.clock import Clock
from library.app.commands.domain.book import BooksRepo
from library.app.commands.domain.issue_loan import IssueLoan
from library.app.commands.domain.loan import (
    LoanAlreadyReturned,
    LoanOverdue,
    LoansRepo,
)
from library.app.commands.domain.reader import ReadersRepo
from library.app.commands.domain.return_loan import ReturnLoan
from library.app.commands.signals import LoanIssued
from library.app.commands.use_cases.loans.extend_loan import (
    ExtendLoan,
    ExtendLoanParams,
)
from library.app.commands.use_cases.loans.issue_loan_command import (
    IssueLoanCommand,
    IssueLoanCommandParams,
)
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    RemindOverdueLoans,
    RemindOverdueLoansParams,
)
from library.app.commands.use_cases.loans.return_loan_command import (
    ReturnLoanCommand,
    ReturnLoanCommandParams,
)
from library.app.queries.loans.find_loans import FindLoansParams
from library.app.roles import Account, PermissionDenied

from tests.unit.app.conftest import FakeOutbox, SignalsCollector


@pytest.fixture
def issue_command(
    in_memory_readers_repo: ReadersRepo,
    in_memory_books_repo: BooksRepo,
    in_memory_loans_repo: LoansRepo,
    clock: Clock,
    hub: Hub,
    logger: logging.Logger,
) -> IssueLoanCommand:
    issue_loan = IssueLoan(
        readers=in_memory_readers_repo,
        books=in_memory_books_repo,
        loans=in_memory_loans_repo,
    )
    return IssueLoanCommand(issue_loan=issue_loan, clock=clock, hub=hub, logger=logger)


def test_issue_loan_emits_signal(
    issue_command: IssueLoanCommand,
    in_memory_loans_repo: LoansRepo,
    add_reader: Callable[..., int],
    add_book: Callable[..., int],
    hub: Hub,
    admin: Account,
    today: date,
) -> None:
    signals = SignalsCollector(hub, LoanIssued)
    reader_id, book_id = add_reader(), add_book()
    params = IssueLoanCommandParams(
        reader_id=reader_id,
        book_id=book_id,
        inventory_number='INV-0',
        days=7,
    )
    loan_id = issue_command.run(params, admin)
    assert signals.received == [LoanIssued(loan_id=loan_id, reader_id=reader_id)]
    assert in_memory_loans_repo.get_by_id(loan_id).period.due == today + timedelta(
        days=7,
    )


def test_issue_loan_permission_denied(
    issue_command: IssueLoanCommand,
    add_reader: Callable[..., int],
    add_book: Callable[..., int],
    in_memory_books_repo: BooksRepo,
    hub: Hub,
    guest: Account,
) -> None:
    signals = SignalsCollector(hub, LoanIssued)
    book_id = add_book()
    params = IssueLoanCommandParams(
        reader_id=add_reader(),
        book_id=book_id,
        inventory_number='INV-0',
    )
    with pytest.raises(PermissionDenied):
        issue_command.run(params, guest)
    assert signals.received == []
    assert in_memory_books_repo.get_by_id(book_id).copies[0].is_available


@pytest.mark.parametrize(
    ('days', 'ok'),
    [(1, True), (60, True), (0, False), (61, False)],
)
def test_issue_params_days_boundary(days: int, ok: bool) -> None:
    def build() -> IssueLoanCommandParams:
        return IssueLoanCommandParams(
            reader_id=1,
            book_id=1,
            inventory_number='X',
            days=days,
        )

    if ok:
        build()
    else:
        with pytest.raises(ValueError):
            build()


@pytest.fixture
def extend_loan(
    in_memory_loans_repo: LoansRepo,
    clock: Clock,
    logger: logging.Logger,
) -> ExtendLoan:
    return ExtendLoan(loans=in_memory_loans_repo, clock=clock, logger=logger)


def test_extend_loan(
    extend_loan: ExtendLoan,
    in_memory_loans_repo: LoansRepo,
    add_loan: Callable[..., int],
    admin: Account,
    today: date,
) -> None:
    loan_id = add_loan(reader_id=1, book_id=1, due_in_days=1)
    extend_loan.run(ExtendLoanParams(loan_id=loan_id, days=5), admin)
    assert in_memory_loans_repo.get_by_id(loan_id).period.due == today + timedelta(
        days=6,
    )


def test_extend_overdue_loan(
    extend_loan: ExtendLoan,
    add_loan: Callable[..., int],
    admin: Account,
) -> None:
    loan_id = add_loan(reader_id=1, book_id=1, due_in_days=-1)
    with pytest.raises(LoanOverdue):
        extend_loan.run(ExtendLoanParams(loan_id=loan_id, days=5), admin)


def test_extend_loan_permission_and_params(
    extend_loan: ExtendLoan,
    add_loan: Callable[..., int],
    guest: Account,
) -> None:
    loan_id = add_loan(reader_id=1, book_id=1)
    with pytest.raises(PermissionDenied):
        extend_loan.run(ExtendLoanParams(loan_id=loan_id, days=5), guest)
    with pytest.raises(ValueError):
        ExtendLoanParams(loan_id=loan_id, days=0)


def test_return_loan_command(
    in_memory_loans_repo: LoansRepo,
    in_memory_books_repo: BooksRepo,
    clock: Clock,
    logger: logging.Logger,
    add_reader: Callable[..., int],
    add_book: Callable[..., int],
    issue_command: IssueLoanCommand,
    admin: Account,
    guest: Account,
) -> None:
    book_id = add_book()
    loan_id = issue_command.run(
        IssueLoanCommandParams(
            reader_id=add_reader(),
            book_id=book_id,
            inventory_number='INV-0',
        ),
        admin,
    )
    command = ReturnLoanCommand(
        return_loan=ReturnLoan(loans=in_memory_loans_repo, books=in_memory_books_repo),
        clock=clock,
        logger=logger,
    )
    with pytest.raises(PermissionDenied):
        command.run(ReturnLoanCommandParams(loan_id=loan_id), guest)
    command.run(ReturnLoanCommandParams(loan_id=loan_id), admin)
    assert in_memory_loans_repo.get_by_id(loan_id).returned()
    assert in_memory_books_repo.get_by_id(book_id).copies[0].is_available
    with pytest.raises(LoanAlreadyReturned):
        command.run(ReturnLoanCommandParams(loan_id=loan_id), admin)


def test_remind_overdue_loans(
    in_memory_loans_repo: LoansRepo,
    outbox: FakeOutbox,
    logger: logging.Logger,
    add_loan: Callable[..., int],
    today: date,
) -> None:
    overdue_id = add_loan(reader_id=7, book_id=1, due_in_days=-1)
    add_loan(reader_id=8, book_id=1, due_in_days=0)
    remind = RemindOverdueLoans(
        loans=in_memory_loans_repo,
        outbox=outbox,
        logger=logger,
    )
    assert remind.run(RemindOverdueLoansParams(on=today)) == 1
    assert [(m[0], m[1], m[2]) for m in outbox.messages] == [
        ('overdue_reminder', 7, overdue_id),
    ]


def test_find_loans_params() -> None:
    FindLoansParams(limit=100)
    with pytest.raises(ValueError):
        FindLoansParams(limit=101)
    with pytest.raises(ValueError):
        FindLoansParams(offset=-1)
