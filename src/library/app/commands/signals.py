from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LoanIssued:
    loan_id: int
    reader_id: int


@dataclass(frozen=True)
class OverdueReminderRequested:
    on: date
