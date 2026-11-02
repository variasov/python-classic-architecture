from classic.signals import Hub
from library.app.clock import Clock
from library.app.commands.signals import OverdueReminderRequested


class RequestOverdueReminder:
    """Задача планировщика: просит напомнить о просрочках на сегодня."""

    def __init__(self, hub: Hub, clock: Clock) -> None:
        self._hub = hub
        self._clock = clock

    def __call__(self) -> None:
        self._hub.notify(OverdueReminderRequested(on=self._clock.today()))
