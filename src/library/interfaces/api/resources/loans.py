from dataclasses import dataclass
from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.loans.issue_loan import (
    IssueLoan,
    IssueLoanParams,
)
from library.app.queries.loans.find_loans import (
    FindLoans,
    FindLoansParams,
    LoanListItemDTO,
)
from library.interfaces.api.middleware import current_account


@dataclass(frozen=True)
class LoanCreated:
    """Контракт ответа на выдачу экземпляра."""

    id: int


class LoansResource:
    _query_validator: ClassVar = TypeAdapter(FindLoansParams)
    _loans_serializer: ClassVar = TypeAdapter(list[LoanListItemDTO])
    _create_validator: ClassVar = TypeAdapter(IssueLoanParams)
    _created_serializer: ClassVar = TypeAdapter(LoanCreated)

    def __init__(self, find_loans: FindLoans, issue_loan: IssueLoan) -> None:
        self._find_loans = find_loans
        self._issue_loan = issue_loan

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._query_validator.validate_python(req.params)
        loans = self._find_loans.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._loans_serializer.dump_json(loans)

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        loan_id = self._issue_loan.run(params, current_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(LoanCreated(id=loan_id))
