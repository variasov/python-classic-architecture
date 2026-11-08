from dataclasses import dataclass
from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.loans.issue_loan import (
    IssueLoanCommand,
    IssueLoanCommandParams,
)
from library.app.queries.loans.find_loans import (
    FindLoans,
    FindLoansParams,
    LoanDTO,
)
from library.app.roles import Account


@dataclass(frozen=True)
class LoanCreated:
    id: int


class LoansResource:
    _find_validator: ClassVar[TypeAdapter[FindLoansParams]] = TypeAdapter(
        FindLoansParams,
    )
    _create_validator: ClassVar[TypeAdapter[IssueLoanCommandParams]] = TypeAdapter(
        IssueLoanCommandParams,
    )
    _loans_serializer: ClassVar[TypeAdapter[list[LoanDTO]]] = TypeAdapter(
        list[LoanDTO],
    )
    _created_serializer: ClassVar[TypeAdapter[LoanCreated]] = TypeAdapter(
        LoanCreated,
    )

    def __init__(
        self,
        find_loans: FindLoans,
        issue_loan: IssueLoanCommand,
    ) -> None:
        self._find_loans = find_loans
        self._issue_loan = issue_loan

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
    ) -> None:
        params = self._find_validator.validate_python(req.params)
        loans = self._find_loans.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._loans_serializer.dump_json(loans)

    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
    ) -> None:
        params = self._create_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        loan_id = self._issue_loan.run(account, params)
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(
            LoanCreated(id=loan_id),
        )
