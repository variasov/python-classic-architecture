from classic.scheduler import ScheduledJob, Scheduler

from library.composites.app.commands.remind_overdue_loans import (
    remind_overdue_loans,
)

CRON_SCHEDULE = '0 9 * * *'


def add_overdue_reminder(scheduler: Scheduler) -> ScheduledJob:
    """Регистрирует ежедневную задачу напоминания о просрочке."""
    return scheduler.by_cron(
        schedule=CRON_SCHEDULE,
        job=remind_overdue_loans.run,
    )


def build_scheduler(scheduler: Scheduler) -> Scheduler:
    """Собирает планировщик: регистрирует задачи точки входа."""
    add_overdue_reminder(scheduler)
    return scheduler
