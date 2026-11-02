from classic.db_tools import Engine
from library.app.clock import Clock
from library.app.queries.loans.find_loans import FindLoans, LoansSearchGateway
from library.composites.infra.clock.system import clock as default_clock
from library.composites.infra.db.engine import engine as default_engine
from library.composites.infra.db.gateways.loans_search_gateway import (
    loans_search_gateway,
)


def create_find_loans(
    gateway: LoansSearchGateway,
    clock: Clock,
    engine: Engine,
) -> FindLoans:
    query = FindLoans(gateway=gateway, clock=clock)
    query.run = engine.transaction(query.run)
    return query


find_loans = create_find_loans(
    gateway=loans_search_gateway,
    clock=default_clock,
    engine=default_engine,
)
