from uuid import UUID

from .domain.do_complex_thing import DoComplexThing


class DoSomething:

    def __init__(self, do_complex: DoComplexThing) -> None:
        self.do_complex = do_complex

    def run(self, thing_id: UUID) -> UUID | None:
        """Пример команды, вызывающей доменный usecase"""
        thing = self.do_complex.run(thing_id)
        if thing:
            return thing.id
