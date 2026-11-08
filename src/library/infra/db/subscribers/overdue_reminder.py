from classic.signals import Hub

from library.app.commands.signals import OverdueReminderRequested
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    RemindOverdueLoans,
    RemindOverdueLoansParams,
)


class OverdueReminderSubscriber:
    def __init__(
        self,
        hub: Hub,
        remind_overdue_loans: RemindOverdueLoans,
    ) -> None:
        self._remind_overdue_loans = remind_overdue_loans
        hub.add_reaction(OverdueReminderRequested, self._on_request)

    def _on_request(self, signal: OverdueReminderRequested) -> None:
        self._remind_overdue_loans.run(
            RemindOverdueLoansParams(on=signal.on),
        )
