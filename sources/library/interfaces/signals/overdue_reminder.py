from classic.signals import Hub
from library.app.commands.signals import OverdueReminderRequested
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    RemindOverdueLoans,
    RemindOverdueLoansParams,
)


class OverdueReminderSubscriber:
    """По сигналу запускает команду напоминаний о просрочке."""

    def __init__(self, remind_overdue_loans: RemindOverdueLoans, hub: Hub) -> None:
        self._remind = remind_overdue_loans
        hub.add_reaction(OverdueReminderRequested, self._on_requested)

    def _on_requested(self, signal: OverdueReminderRequested) -> None:
        self._remind.run(RemindOverdueLoansParams(on=signal.on))
