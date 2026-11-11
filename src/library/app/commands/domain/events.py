from dataclasses import dataclass


@dataclass(frozen=True)
class LoanIssued:
    """Событие предметной области: выдача оформлена."""

    loan_id: int
    reader_id: int
