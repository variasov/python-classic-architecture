from dataclasses import dataclass
from datetime import date, timedelta

from classic.signals import Hub

from library.app.commands.domain.copy import CopiesRepo
from library.app.commands.domain.errors import DomainError
from library.app.commands.domain.events import LoanIssued
from library.app.commands.domain.loan import Loan, LoanPeriod, LoansRepo
from library.app.commands.domain.reader import ReadersRepo


@dataclass
class ReaderCannotBorrow(DomainError):
    reader_id: int | None

    def __str__(self) -> str:
        return f'Читатель с id={self.reader_id} не может брать экземпляры'


@dataclass
class LoanLimitReached(DomainError):
    reader_id: int | None
    limit: int

    def __str__(self) -> str:
        return (
            f'Читатель с id={self.reader_id} достиг лимита выдач: {self.limit}'
        )


@dataclass
class ReaderHasOverdueLoans(DomainError):
    reader_id: int | None

    def __str__(self) -> str:
        return f'У читателя с id={self.reader_id} есть просроченные выдачи'


class BorrowCopy:
    """Выдача экземпляра читателю: затрагивает читателя, экземпляр и выдачу"""

    def __init__(
        self,
        readers: ReadersRepo,
        copies: CopiesRepo,
        loans: LoansRepo,
        hub: Hub,
    ) -> None:
        self._readers = readers
        self._copies = copies
        self._loans = loans
        self._hub = hub

    def run(self, reader_id: int, copy_id: int, on: date) -> Loan:
        reader = self._readers.get_by_id(reader_id)
        copy = self._copies.get_by_id(copy_id)
        assert reader.id is not None
        assert copy.id is not None

        if not (reader.membership_active(on=on) and reader.not_blocked()):
            raise ReaderCannotBorrow(reader_id=reader.id)

        active_loans = self._loans.find(
            Loan.of_reader(reader_id=reader.id) & ~Loan.returned()
        )
        limit = reader.membership.loan_limit
        if len(active_loans) >= limit:
            raise LoanLimitReached(reader_id=reader.id, limit=limit)

        overdue_loans = self._loans.find(
            Loan.of_reader(reader_id=reader.id) & Loan.overdue(on=on)
        )
        if overdue_loans:
            raise ReaderHasOverdueLoans(reader_id=reader.id)

        copy.take()
        self._copies.save(copy)

        loan = Loan(
            reader_id=reader.id,
            copy_id=copy.id,
            period=LoanPeriod(
                start=on, due=on + timedelta(days=Loan.TERM_DAYS)
            ),
        )
        self._loans.save(loan)
        assert loan.id is not None
        self._hub.notify(LoanIssued(loan_id=loan.id, reader_id=reader.id))
        return loan
