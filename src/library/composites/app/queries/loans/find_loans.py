import pydantic

from library.app.queries.loans.find_loans import FindLoans
from library.composites.infra.db.gateways.find_loans import find_loans_gateway

find_loans = FindLoans(gateway=find_loans_gateway)
find_loans.run = pydantic.validate_call(find_loans.run)  # pyright: ignore[reportAttributeAccessIssue]
