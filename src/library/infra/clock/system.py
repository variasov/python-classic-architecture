from datetime import datetime, timezone

from library.app.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)
