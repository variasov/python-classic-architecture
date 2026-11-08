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


class LoansRepository(LoansRepo):
    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Loan:
        loan = (
            self._db.query_from('aggregates/loans/get_by_id.sql')
            .map_to(
                Loan,
                loan=Entity(
                    Loan,
                    'id',
                    period=Assign('period'),
                    extensions=Append(Extension),
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
        loan_id = loan.id
        if loan_id is None:
            loan_id = int(
                self._db.query_from('aggregates/loans/insert.sql').scalar(
                    reader_id=loan.reader_id,
                    book_id=loan.book_id,
                    inventory_number=loan.inventory_number,
                    issued_at=loan.issued_at,
                    start_date=loan.period.start,
                    due_date=loan.period.due,
                    returned_at=loan.returned_at,
                ),
            )
            loan.id = loan_id
        else:
            row = (
                self._db.query_from('aggregates/loans/update.sql')
                .execute(
                    id=loan_id,
                    reader_id=loan.reader_id,
                    book_id=loan.book_id,
                    inventory_number=loan.inventory_number,
                    issued_at=loan.issued_at,
                    start_date=loan.period.start,
                    due_date=loan.period.due,
                    returned_at=loan.returned_at,
                )
                .fetchone()
            )
            if row is None:
                raise LoanNotFound(id=loan_id)
        self._sync_extensions(loan_id, loan)
        return loan

    def find(self, criteria: Criteria[Loan]) -> list[Loan]:
        loans: list[Loan] = (
            self._db.query_from('aggregates/loans/find.sql.tmpl')
            .map_to(
                Loan,
                loan=Entity(
                    Loan,
                    'id',
                    period=Assign('period'),
                    extensions=Append(Extension),
                ),
                period=Value(LoanPeriod),
                extension=Value(Extension),
            )
            .all(criteria=criteria)
        )
        return loans

    def _sync_extensions(self, loan_id: int, loan: Loan) -> None:
        for extension in loan.extensions:
            self._db.query_from(
                'aggregates/loans/upsert_extension.sql',
            ).execute(
                loan_id=loan_id,
                extended_at=extension.extended_at,
                new_due=extension.new_due,
            )
        self._db.query_from(
            'aggregates/loans/delete_missing_extensions.sql',
        ).execute(
            loan_id=loan_id,
            extended_at=[extension.extended_at for extension in loan.extensions],
            new_due=[extension.new_due for extension in loan.extensions],
        )
