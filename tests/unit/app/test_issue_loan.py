import logging
from datetime import date

import pytest

from library.app.commands.domain.book import BookNotFound
from library.app.commands.domain.issue_loan import IssueLoan
from library.app.commands.domain.loan import LoanNotFound
from library.app.commands.domain.reader import ReaderNotFound
from library.app.commands.signals import LoanIssued
from library.app.commands.use_cases.loans.issue_loan import IssueLoanCommand
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date(2026, 3, 10)


def test_issue_loan_command_emits_signal(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    hub,
    account,
    book_factory,
    reader_factory,
    issue_loan_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    issue_loan = IssueLoan(
        readers=in_memory_readers_repo,
        books=in_memory_books_repo,
        loans=in_memory_loans_repo,
    )
    usecase = IssueLoanCommand(
        issue_loan=issue_loan,
        clock=clock_factory(TODAY),
        hub=hub,
        logger=test_logger,
    )
    received: list[LoanIssued] = []
    hub.add_reaction(LoanIssued, received.append)
    loan_id = usecase.run(
        account,
        issue_loan_params_factory(
            reader_id=reader.id,
            book_id=book.id,
        ),
    )
    assert received == [
        LoanIssued(loan_id=loan_id, reader_id=reader.id),
    ]
    assert in_memory_loans_repo.get_by_id(loan_id).reader_id == reader.id
    assert in_memory_books_repo.get_by_id(book.id).copies[0].is_available is False
    record = caplog.records[0]
    assert record.msg == 'Выдана книга, выдача id=%s'
    assert record.args == (loan_id,)


def test_issue_loan_command_requires_permission(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    hub,
    book_factory,
    reader_factory,
    issue_loan_params_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    reader = in_memory_readers_repo.save(reader_factory())
    issue_loan = IssueLoan(
        readers=in_memory_readers_repo,
        books=in_memory_books_repo,
        loans=in_memory_loans_repo,
    )
    usecase = IssueLoanCommand(
        issue_loan=issue_loan,
        clock=clock_factory(TODAY),
        hub=hub,
        logger=test_logger,
    )
    received: list[LoanIssued] = []
    hub.add_reaction(LoanIssued, received.append)
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            issue_loan_params_factory(
                reader_id=reader.id,
                book_id=book.id,
            ),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.LOANS_EDIT
    assert received == []
    with pytest.raises(LoanNotFound):
        in_memory_loans_repo.get_by_id(1)


def test_issue_loan_command_propagates_domain_error(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    hub,
    account,
    book_factory,
    issue_loan_params_factory,
) -> None:
    book = in_memory_books_repo.save(book_factory())
    issue_loan = IssueLoan(
        readers=in_memory_readers_repo,
        books=in_memory_books_repo,
        loans=in_memory_loans_repo,
    )
    usecase = IssueLoanCommand(
        issue_loan=issue_loan,
        clock=clock_factory(TODAY),
        hub=hub,
        logger=test_logger,
    )
    with pytest.raises(ReaderNotFound):
        usecase.run(
            account,
            issue_loan_params_factory(
                reader_id=999,
                book_id=book.id,
            ),
        )


def test_issue_loan_command_unknown_book(
    in_memory_books_repo,
    in_memory_readers_repo,
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    hub,
    account,
    reader_factory,
    issue_loan_params_factory,
) -> None:
    reader = in_memory_readers_repo.save(reader_factory())
    issue_loan = IssueLoan(
        readers=in_memory_readers_repo,
        books=in_memory_books_repo,
        loans=in_memory_loans_repo,
    )
    usecase = IssueLoanCommand(
        issue_loan=issue_loan,
        clock=clock_factory(TODAY),
        hub=hub,
        logger=test_logger,
    )
    with pytest.raises(BookNotFound):
        usecase.run(
            account,
            issue_loan_params_factory(reader_id=reader.id),
        )
