from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.loans.return_loan import (
    ReturnLoan,
    ReturnLoanParams,
)
from library.interfaces.api.middleware import current_account


class ReturnsResource:
    _return_validator: ClassVar = TypeAdapter(ReturnLoanParams)

    def __init__(self, return_loan: ReturnLoan) -> None:
        self._return_loan = return_loan

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._return_validator.validate_json(req.bounded_stream.read())
        self._return_loan.run(params, current_account(req))
