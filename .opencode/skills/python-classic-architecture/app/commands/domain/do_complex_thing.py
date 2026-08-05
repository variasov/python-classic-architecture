from uuid import UUID

from .aggregates.another_thing import AnotherThingsRepo
from .aggregates.thing import Thing, ThingsRepo


class DoComplexThing:

    def __init__(
        self,
        things: ThingsRepo,
        another_things: AnotherThingsRepo,
    ) -> None:
        self.things = things
        self.another_things = another_things

    def run(self, anoth_thing_id: UUID) -> Thing | None:
        """Пример доменного usecase, обращающегося к разным агрегатам"""

        another_thing = self.another_things.get_by_id(anoth_thing_id)
        if not another_thing.thing_id:
            return

        thing = self.things.get_by_id(another_thing.thing_id)
        thing.clean_items('')

        return thing
