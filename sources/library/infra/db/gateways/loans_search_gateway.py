from dataclasses import asdict
from datetime import date
from typing import cast

from classic.db_tools import Engine, Entity
from library.app.queries.loans.find_loans import (
    FindLoansParams,
    FoundLoan,
    LoansSearchGateway,
)


class DbLoansSearchGateway(LoansSearchGateway):
    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def find(self, params: FindLoansParams, today: date) -> list[FoundLoan]:
        return cast(
            'list[FoundLoan]',
            list(
                self._db.query_from('gateways/loans/find.sql.tmpl')
                .map_to(FoundLoan, FoundLoan=Entity(FoundLoan, 'id'))
                .all({**asdict(params), 'today': today}),
            ),
        )
