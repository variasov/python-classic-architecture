from typing import Any

from classic.db_tools import Engine

from library.app.clock import Clock
from library.app.queries.loans.find_loans import (
    FindLoans,
    FindLoansGateway,
)
from library.composites.infra.clock.system import clock
from library.composites.infra.db.engine import engine
from library.composites.infra.db.gateways.find_loans import find_loans_gateway


def create_find_loans(
    gateway: FindLoansGateway,
    clock_: Clock,
    engine_: Engine[Any],
) -> FindLoans:
    usecase = FindLoans(gateway=gateway, clock=clock_)
    usecase.run = engine_.transaction(usecase.run)
    return usecase


find_loans = create_find_loans(
    gateway=find_loans_gateway,
    clock_=clock,
    engine_=engine,
)
