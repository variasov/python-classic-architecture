from collections.abc import Callable

from library.app.commands.signals import OverdueReminderRequested
from library.composites.app.hub import hub
from library.composites.infra.clock.system import clock
from library.composites.infra.db.subscribers import (  # noqa: F401
    overdue_reminder,  # pyright: ignore[reportUnusedImport]
)

jobs: list[Callable[[], None]] = []


def request_overdue_reminders() -> None:
    hub.notify(OverdueReminderRequested(on=clock.today()))


jobs.append(request_overdue_reminders)
