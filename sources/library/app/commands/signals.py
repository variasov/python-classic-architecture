from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LoanIssued:
    """Читателю выдан экземпляр."""

    loan_id: int
    reader_id: int


@dataclass(frozen=True)
class OverdueReminderRequested:
    """Нужно напомнить о просроченных на дату `on` выдачах."""

    on: date
