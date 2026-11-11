from datetime import date
from typing import Any

from classic.db_tools import Engine, Entity

from library.app.queries.loans.find_loans import (
    FindLoansGateway,
    FindLoansParams,
    LoanListItemDTO,
)


class DbFindLoansGateway(FindLoansGateway):
    """Список выдач из PostgreSQL."""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def run(
        self,
        params: FindLoansParams,
        on: date,
    ) -> list[LoanListItemDTO]:
        loans: list[LoanListItemDTO] = (
            self._db.query_from('gateways/loans/find_loans.sql.tmpl')
            .map_to(
                LoanListItemDTO,
                LoanListItemDTO=Entity(LoanListItemDTO, 'id'),
            )
            .all(
                reader_id=params.reader_id,
                only_overdue=params.only_overdue,
                only_active=params.only_active,
                on=on,
                limit=params.limit,
                offset=params.offset,
            )
        )
        return loans
