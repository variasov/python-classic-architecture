from classic.scheduler import Scheduler

from library.composites.app.commands.remind_overdue_loans import (
    remind_overdue_loans,
)

scheduler = Scheduler()
scheduler.by_cron('0 9 * * *', remind_overdue_loans.run)
