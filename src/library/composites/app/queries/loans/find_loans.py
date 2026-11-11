from library.app.queries.loans.find_loans import FindLoans
from library.composites.infra.db.gateways.find_loans import find_loans_gateway

find_loans = FindLoans(gateway=find_loans_gateway)
