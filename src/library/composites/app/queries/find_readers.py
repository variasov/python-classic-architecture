from typing import Any

from classic.db_tools import Engine

from library.app.clock import Clock
from library.app.queries.readers.find_readers import (
    FindReaders,
    FindReadersGateway,
)
from library.composites.infra.clock.system import clock
from library.composites.infra.db.engine import engine
from library.composites.infra.db.gateways.find_readers import (
    find_readers_gateway,
)


def create_find_readers(
    gateway: FindReadersGateway,
    clock_: Clock,
    engine_: Engine[Any],
) -> FindReaders:
    usecase = FindReaders(gateway=gateway, clock=clock_)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


find_readers = create_find_readers(
    gateway=find_readers_gateway,
    clock_=clock,
    engine_=engine,
)
