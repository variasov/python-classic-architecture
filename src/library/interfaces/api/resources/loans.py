from dataclasses import dataclass
from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.loans.issue_loan import (
    IssueLoan,
    IssueLoanParams,
)
from library.interfaces.api.middleware import current_account


@dataclass(frozen=True)
class LoanCreated:
    """Контракт ответа на выдачу экземпляра"""

    id: int


class LoansResource:
    _create_validator: ClassVar = TypeAdapter(IssueLoanParams)
    _created_serializer: ClassVar = TypeAdapter(LoanCreated)

    def __init__(self, issue_loan: IssueLoan) -> None:
        self._issue_loan = issue_loan

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        loan_id = self._issue_loan.run(params, current_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(LoanCreated(id=loan_id))
