from library.composites.app.commands.remind_overdue_loans import (
    remind_overdue_loans,
)
from library.composites.app.hub import hub
from library.infra.db.subscribers.overdue_reminder import (
    OverdueReminderSubscriber,
)

overdue_reminder_subscriber = OverdueReminderSubscriber(
    hub=hub,
    remind_overdue_loans=remind_overdue_loans,
)
