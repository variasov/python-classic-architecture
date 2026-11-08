import logging
from datetime import date

import pytest

from library.app.commands.domain.loan import LoanNotFound
from library.app.commands.domain.return_loan import ReturnLoan
from library.app.commands.use_cases.loans.return_loan import ReturnLoanCommand
from library.app.roles import Account, PermissionDenied, Permissions

TODAY = date(2026, 3, 10)


def test_return_loan_command_returns_copy(
    in_memory_books_repo,
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    account,
    book_factory,
    copy_factory,
    loan_factory,
    return_loan_params_factory,
    caplog,
) -> None:
    caplog.set_level(logging.INFO)
    book = in_memory_books_repo.save(
        book_factory(copies=[copy_factory(is_available=False)]),
    )
    loan = in_memory_loans_repo.save(
        loan_factory(book_id=book.id, inventory_number='INV-1'),
    )
    usecase = ReturnLoanCommand(
        return_loan=ReturnLoan(
            books=in_memory_books_repo,
            loans=in_memory_loans_repo,
        ),
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    usecase.run(account, return_loan_params_factory(loan_id=loan.id))
    assert in_memory_loans_repo.get_by_id(loan.id).returned_at == TODAY
    assert in_memory_books_repo.get_by_id(book.id).copies[0].is_available is True
    record = caplog.records[0]
    assert record.msg == 'Возвращена выдача с id=%s'
    assert record.args == (loan.id,)


def test_return_loan_command_unknown_loan(
    in_memory_books_repo,
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    account,
    return_loan_params_factory,
) -> None:
    usecase = ReturnLoanCommand(
        return_loan=ReturnLoan(
            books=in_memory_books_repo,
            loans=in_memory_loans_repo,
        ),
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    with pytest.raises(LoanNotFound):
        usecase.run(account, return_loan_params_factory())


def test_return_loan_command_requires_permission(
    in_memory_books_repo,
    in_memory_loans_repo,
    clock_factory,
    test_logger,
    book_factory,
    copy_factory,
    loan_factory,
    return_loan_params_factory,
) -> None:
    book = in_memory_books_repo.save(
        book_factory(copies=[copy_factory(is_available=False)]),
    )
    loan = in_memory_loans_repo.save(
        loan_factory(book_id=book.id, inventory_number='INV-1'),
    )
    usecase = ReturnLoanCommand(
        return_loan=ReturnLoan(
            books=in_memory_books_repo,
            loans=in_memory_loans_repo,
        ),
        clock=clock_factory(TODAY),
        logger=test_logger,
    )
    with pytest.raises(PermissionDenied) as exc_info:
        usecase.run(
            Account(login='guest', permissions=frozenset()),
            return_loan_params_factory(loan_id=loan.id),
        )
    assert exc_info.value.login == 'guest'
    assert exc_info.value.permission == Permissions.LOANS_EDIT
    assert in_memory_books_repo.get_by_id(book.id).copies[0].is_available is False
