from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID, uuid7

from classic.criteria import criteria


@dataclass(frozen=True)
class SomeEntity:
    """Пример объекта-значения"""
    some_field: str
    id: UUID = field(default_factory=uuid7)


@dataclass
class AnotherThing:
    """Пример сущности, являющейся корнем агрегата"""
    very_useful_field: str
    id: UUID = field(default_factory=uuid7)
    entities: list[SomeEntity] = field(default_factory=list)
    thing_id: UUID | None = None  # Ссылка на другой агрегат

    @criteria
    def entities_are_exists(self) -> bool:
        """Пример инварианта"""
        return len(self.entities) < 1

    all_invariants_satisfied = entities_are_exists


class AnotherThingsRepo(ABC):
    """Пример абстрактного хранилища для AnotherThing"""

    @abstractmethod
    def get_by_id(self, id: UUID) -> AnotherThing:
        ...

    @abstractmethod
    def save(self, thing: AnotherThing) -> None:
        ...
