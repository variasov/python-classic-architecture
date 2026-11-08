from abc import ABC, abstractmethod
from datetime import date, datetime


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...

    def today(self) -> date:
        return self.now().date()
