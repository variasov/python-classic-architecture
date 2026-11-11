from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.loans.extend_loan import (
    ExtendLoan,
    ExtendLoanParams,
)
from library.interfaces.api.middleware import current_account


class LoanExtensionsResource:
    _extend_validator: ClassVar = TypeAdapter(ExtendLoanParams)

    def __init__(self, extend_loan: ExtendLoan) -> None:
        self._extend_loan = extend_loan

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._extend_validator.validate_json(req.bounded_stream.read())
        self._extend_loan.run(params, current_account(req))
