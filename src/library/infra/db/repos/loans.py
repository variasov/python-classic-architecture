from typing import Any

from classic.criteria import Criteria
from classic.db_tools import Append, Assign, Engine, Entity, Value

from library.app.commands.domain.loan import (
    Extension,
    Loan,
    LoanNotFound,
    LoanPeriod,
    LoansRepo,
)


class DbLoansRepo(LoansRepo):
    """Репозиторий выдач поверх PostgreSQL"""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Loan:
        loan: Loan | None = (
            self._db.query_from('aggregates/loans/get_by_id.sql')
            .map_to(
                Loan,
                Loan=Entity(
                    Loan,
                    'id',
                    period=Assign('period'),
                    extensions=Append('extension'),
                ),
                period=Value(LoanPeriod),
                extension=Value(Extension),
            )
            .one(id=id)
        )
        if loan is None:
            raise LoanNotFound(id=id)
        return loan

    def save(self, loan: Loan) -> Loan:
        loan.check()
        params = self._params(loan)
        if loan.id is None:
            loan.id = self._db.query_from('aggregates/loans/insert.sql').scalar(
                **params
            )
        else:
            updated = self._db.query_from('aggregates/loans/update.sql').scalar(
                **params
            )
            if updated is None:
                raise LoanNotFound(id=loan.id)
        self._sync_extensions(loan)
        return loan

    def find(self, criteria: Criteria[Loan]) -> list[Loan]:
        loans: list[Loan] = (
            self._db.query_from('aggregates/loans/find.sql.tmpl')
            .map_to(
                Loan,
                Loan=Entity(
                    Loan,
                    'id',
                    period=Assign('period'),
                    extensions=Append('extension'),
                ),
                period=Value(LoanPeriod),
                extension=Value(Extension),
            )
            .all(criteria=criteria)
        )
        return loans

    def _sync_extensions(self, loan: Loan) -> None:
        assert loan.id is not None
        self._db.query_from('aggregates/loans/delete_extensions.sql').execute(
            loan_id=loan.id
        )
        rows = [
            {
                'loan_id': loan.id,
                'position': position,
                'extended_at': extension.extended_at,
                'new_due': extension.new_due,
            }
            for position, extension in enumerate(loan.extensions)
        ]
        self._db.query_from('aggregates/loans/insert_extensions.sql').executemany(
            rows
        )

    def _params(self, loan: Loan) -> dict[str, Any]:
        return {
            'id': loan.id,
            'reader_id': loan.reader_id,
            'copy_id': loan.copy_id,
            'period_start': loan.period.start,
            'period_due': loan.period.due,
            'returned_at': loan.returned_at,
        }
