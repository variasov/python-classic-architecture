from library.composites.app.commands.loans.issue_loan import issue_loan
from library.composites.app.queries.loans.find_loans import find_loans
from library.interfaces.web_api.resources.loans import LoansResource

loans = LoansResource(find_loans=find_loans, issue_loan=issue_loan)
