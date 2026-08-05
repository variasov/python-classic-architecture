from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID, uuid7

from classic.criteria import criteria


@dataclass(frozen=True)
class Item:
    """Пример объекта-значения"""
    some_field: str
    another: str


@dataclass
class Thing:
    """Пример сущности, являющейся корнем агрегата"""
    very_useful_field: str
    id: UUID = field(default_factory=uuid7)
    items: list[Item] = field(default_factory=list)

    @criteria
    def items_are_exists(self) -> bool:
        """Пример инварианта"""
        return len(self.items) > 0

    @criteria
    def very_useful_field_not_empty(self) -> bool:
        """Пример инварианта"""
        return self.very_useful_field != ''

    all_invariants_satisfied = (
        items_are_exists() & very_useful_field_not_empty()
    )  # Полное выражение, которое проверит весь агрегат

    def clean_items(self, some_field: str):
        """Пример логики, работающей с содеримым агрегата"""
        self.items = [
            item for item in self.items
            if item.some_field == some_field
        ]


class ThingsRepo(ABC):
    """Пример абстрактного хранилища для Thing"""

    @abstractmethod
    def get_by_id(self, id: UUID) -> Thing:
        ...

    @abstractmethod
    def save(self, thing: Thing) -> None:
        ...
