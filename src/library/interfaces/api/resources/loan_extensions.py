from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.loans.extend_loan import (
    ExtendLoan,
    ExtendLoanParams,
)
from library.app.roles import Account


class LoanExtensionsResource:
    _params_validator: ClassVar[TypeAdapter[ExtendLoanParams]] = TypeAdapter(
        ExtendLoanParams,
    )

    def __init__(self, extend_loan: ExtendLoan) -> None:
        self._extend_loan = extend_loan

    def on_post(
        self,
        req: falcon.Request,
        _resp: falcon.Response,
    ) -> None:
        params = self._params_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        self._extend_loan.run(account, params)
