from datetime import date

from library.app.domain.copy import CopiesRepo
from library.app.domain.loan import LoansRepo


class ReturnCopy:
    """Возврат экземпляра: затрагивает выдачу и экземпляр."""

    def __init__(self, loans: LoansRepo, copies: CopiesRepo) -> None:
        self._loans = loans
        self._copies = copies

    def run(self, loan_id: int, on: date) -> None:
        loan = self._loans.get_by_id(loan_id)
        loan.close(on=on)
        copy = self._copies.get_by_id(loan.copy_id)
        copy.give_back()
        self._loans.save(loan)
        self._copies.save(copy)
