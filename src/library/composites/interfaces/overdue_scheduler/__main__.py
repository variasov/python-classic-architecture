from classic.scheduler import Scheduler

from library.composites.interfaces.overdue_scheduler.jobs import (
    request_overdue_reminders,
)

scheduler = Scheduler()
scheduler.by_cron(
    schedule='0 9 * * *',
    job=request_overdue_reminders,
)
scheduler.run()
