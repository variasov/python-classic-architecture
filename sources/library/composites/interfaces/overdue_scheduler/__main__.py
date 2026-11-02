from classic.scheduler import Scheduler
from library.composites.interfaces.overdue_scheduler.jobs import (
    request_overdue_reminder,
)
from library.composites.interfaces.overdue_scheduler.settings import (
    overdue_scheduler_settings,
)

scheduler = Scheduler()
scheduler.by_cron(  # pyright: ignore[reportUnknownMemberType] - библиотека без аннотаций
    schedule=overdue_scheduler_settings.OVERDUE_CRON,
    job=request_overdue_reminder,
    task_name='OVERDUE_REMINDER',
)
scheduler.run()
