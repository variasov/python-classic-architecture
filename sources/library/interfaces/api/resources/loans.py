from dataclasses import dataclass
from typing import ClassVar

import falcon
from library.app.commands.use_cases.loans.extend_loan import (
    ExtendLoan,
    ExtendLoanParams,
)
from library.app.commands.use_cases.loans.issue_loan_command import (
    IssueLoanCommand,
    IssueLoanCommandParams,
)
from library.app.commands.use_cases.loans.return_loan_command import (
    ReturnLoanCommand,
    ReturnLoanCommandParams,
)
from library.app.queries.loans.find_loans import (
    FindLoans,
    FindLoansParams,
    FoundLoan,
)
from library.interfaces.api.middleware import get_account
from pydantic import TypeAdapter


@dataclass(frozen=True)
class LoanCreated:
    """Контракт ответа на выдачу: usecase возвращает только id."""

    id: int


class LoansResource:
    _query_validator: ClassVar = TypeAdapter(FindLoansParams)
    _create_validator: ClassVar = TypeAdapter(IssueLoanCommandParams)
    _loans_serializer: ClassVar = TypeAdapter(list[FoundLoan])
    _created_serializer: ClassVar = TypeAdapter(LoanCreated)

    def __init__(self, find_loans: FindLoans, issue_loan: IssueLoanCommand) -> None:
        self._find_loans = find_loans
        self._issue_loan = issue_loan

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._query_validator.validate_python(req.params)
        loans = self._find_loans.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._loans_serializer.dump_json(loans)

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        loan_id = self._issue_loan.run(params, get_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(LoanCreated(id=loan_id))


class LoanExtensionsResource:
    _create_validator: ClassVar = TypeAdapter(ExtendLoanParams)

    def __init__(self, extend_loan: ExtendLoan) -> None:
        self._extend_loan = extend_loan

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        self._extend_loan.run(params, get_account(req))


class ReturnsResource:
    _create_validator: ClassVar = TypeAdapter(ReturnLoanCommandParams)

    def __init__(self, return_loan: ReturnLoanCommand) -> None:
        self._return_loan = return_loan

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        self._return_loan.run(params, get_account(req))
