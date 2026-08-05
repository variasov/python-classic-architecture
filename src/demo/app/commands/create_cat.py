from dataclasses import dataclass
from uuid import uuid4

from classic.criteria import CriteriaNotSatisfied

from demo.app.commands.domain.aggregates.cat import Cat, CatRepository, Movement


@dataclass
class CreateCatDTO:
    name: str
    age: int
    mood: str
    movements: list[Movement] | None = None


class CreateCat:

    def __init__(self, repository: CatRepository) -> None:
        self._repository = repository

    def run(self, dto: CreateCatDTO) -> Cat:
        cat = Cat(
            id=str(uuid4()),
            name=dto.name,
            age=dto.age,
            mood=dto.mood,
        )
        for m in (dto.movements or []):
            cat.add_movement(m)
        try:
            cat.all_invariants_satisfied.must_be_satisfied()
        except CriteriaNotSatisfied:
            raise ValueError('Cat invariants not satisfied')
        self._repository.save(cat)
        return cat
