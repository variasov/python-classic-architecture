from classic.scheduler import Scheduler

from library.composites.interfaces.overdue_scheduler.scheduler import (
    build_scheduler,
)

build_scheduler(Scheduler()).run()
