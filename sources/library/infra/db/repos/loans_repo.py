from dataclasses import dataclass, field
from datetime import date
from typing import Any, cast

from classic.criteria import Criteria
from classic.db_tools import Append, Engine, Entity, Value
from library.app.commands.domain.loan import (
    Extension,
    Loan,
    LoanNotFound,
    LoanPeriod,
    LoansRepo,
)


@dataclass
class LoanRow:
    """Плоская строка выдачи: маппер собирает вложенные коллекции только в классы."""

    id: int
    reader_id: int
    book_id: int
    inventory_number: str
    issued_at: date
    returned_at: date | None
    start: date
    due: date
    extensions: list[Extension] = field(default_factory=list[Extension])

    def to_loan(self) -> Loan:
        return Loan(
            id=self.id,
            reader_id=self.reader_id,
            book_id=self.book_id,
            inventory_number=self.inventory_number,
            issued_at=self.issued_at,
            returned_at=self.returned_at,
            period=LoanPeriod(start=self.start, due=self.due),
            extensions=self.extensions,
        )


class DbLoansRepo(LoansRepo):
    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def get_by_id(self, id: int) -> Loan:
        row = cast(
            'LoanRow | None',
            self._db.query_from('aggregates/loans/get_by_id.sql')
            .map_to(
                LoanRow,
                LoanRow=Entity(LoanRow, 'id', extensions=Append('extension')),
                Extension=Value(Extension),
            )
            .one(id=id),
        )
        if row is None:
            raise LoanNotFound(id=id)
        return row.to_loan()

    def save(self, loan: Loan) -> Loan:
        loan.check()
        params: dict[str, Any] = {
            'reader_id': loan.reader_id,
            'book_id': loan.book_id,
            'inventory_number': loan.inventory_number,
            'issued_at': loan.issued_at,
            'start': loan.period.start,
            'due': loan.period.due,
            'returned_at': loan.returned_at,
        }
        if loan.id is None:
            loan.id = self._db.query_from('aggregates/loans/insert.sql').scalar(params)
        else:
            updated_id = self._db.query_from('aggregates/loans/update.sql').scalar(
                {'id': loan.id, **params},
            )
            if updated_id is None:
                raise LoanNotFound(id=loan.id)
        self._sync_extensions(cast('int', loan.id), loan)
        return loan

    def find(self, criteria: Criteria[Loan]) -> list[Loan]:
        ids = self._db.query_from('aggregates/loans/find_ids.sql.tmpl').scalars(
            criteria=criteria,
        )
        return [self.get_by_id(loan_id) for loan_id in ids]

    def _sync_extensions(self, loan_id: int, loan: Loan) -> None:
        for position, extension in enumerate(loan.extensions):
            self._db.query_from('aggregates/loans/upsert_extension.sql').execute(
                loan_id=loan_id,
                position=position,
                extended_at=extension.extended_at,
                new_due=extension.new_due,
            )
        self._db.query_from('aggregates/loans/delete_missing_extensions.sql').execute(
            loan_id=loan_id,
            count=len(loan.extensions),
        )
