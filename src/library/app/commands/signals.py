from dataclasses import dataclass


@dataclass(frozen=True)
class LoanIssued:
    """Сигнал: выдача экземпляра оформлена."""

    loan_id: int
    reader_id: int
