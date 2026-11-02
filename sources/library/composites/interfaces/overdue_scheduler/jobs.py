from library.composites.app.commands.remind_overdue_loans import remind_overdue_loans
from library.composites.app.hub import hub
from library.composites.infra.clock.system import clock
from library.interfaces.overdue_scheduler.job import RequestOverdueReminder
from library.interfaces.signals.overdue_reminder import OverdueReminderSubscriber

# Импорт подписывает обработчик на сигнал OverdueReminderRequested
overdue_reminder_subscriber = OverdueReminderSubscriber(
    remind_overdue_loans=remind_overdue_loans,
    hub=hub,
)

request_overdue_reminder = RequestOverdueReminder(hub=hub, clock=clock)
