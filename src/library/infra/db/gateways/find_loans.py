from datetime import date
from typing import Any

from classic.db_tools import Engine, Value

from library.app.queries.loans.find_loans import (
    FindLoansGateway,
    FindLoansParams,
    LoanDTO,
)


class FindLoansGatewayImpl(FindLoansGateway):
    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def find(
        self,
        params: FindLoansParams,
        on: date,
    ) -> list[LoanDTO]:
        loans: list[LoanDTO] = (
            self._db.query_from('gateways/loans/find.sql.tmpl')
            .map_to(LoanDTO, loandto=Value(LoanDTO))
            .all(
                reader_id=params.reader_id,
                only_overdue=params.only_overdue,
                only_active=params.only_active,
                on=on,
            )
        )
        return loans
