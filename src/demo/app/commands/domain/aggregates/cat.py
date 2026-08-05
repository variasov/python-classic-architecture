from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from classic.criteria import criteria


@dataclass(frozen=True)
class Movement:
    timestamp: str
    latitude: float
    longitude: float


@dataclass
class Cat:
    id: str
    name: str
    age: int
    mood: str
    movements: list[Movement] = field(default_factory=list)

    def add_movement(self, movement: Movement) -> None:
        self.movements.append(movement)

    @criteria
    def age_is_non_negative(self) -> bool:
        return self.age >= 0

    @criteria
    def name_not_empty(self) -> bool:
        return self.name.strip() != ''

    @criteria
    def mood_not_empty(self) -> bool:
        return self.mood.strip() != ''

    all_invariants_satisfied = (
        age_is_non_negative() & name_not_empty() & mood_not_empty()
    )


class CatRepository(ABC):

    @abstractmethod
    def save(self, cat: Cat) -> None:
        ...
