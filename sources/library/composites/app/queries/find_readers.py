from classic.db_tools import Engine
from library.app.clock import Clock
from library.app.queries.readers.find_readers import FindReaders, ReadersSearchGateway
from library.composites.infra.clock.system import clock as default_clock
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.gateways.readers_search_gateway import (
    readers_search_gateway,
)


def create_find_readers(
    gateway: ReadersSearchGateway,
    clock: Clock,
    engine: Engine,
) -> FindReaders:
    query = FindReaders(gateway=gateway, clock=clock)
    query.run = engine.transaction(query.run)
    return query


find_readers = create_find_readers(
    gateway=readers_search_gateway,
    clock=default_clock,
    engine=default_engine,
)
