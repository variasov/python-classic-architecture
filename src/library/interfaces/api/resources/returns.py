from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.loans.return_loan import (
    ReturnLoanCommand,
    ReturnLoanCommandParams,
)
from library.app.roles import Account


class ReturnsResource:
    _params_validator: ClassVar[TypeAdapter[ReturnLoanCommandParams]] = TypeAdapter(
        ReturnLoanCommandParams,
    )

    def __init__(self, return_loan: ReturnLoanCommand) -> None:
        self._return_loan = return_loan

    def on_post(
        self,
        req: falcon.Request,
        _resp: falcon.Response,
    ) -> None:
        params = self._params_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        self._return_loan.run(account, params)
