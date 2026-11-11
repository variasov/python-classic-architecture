from library.composites.app.commands.issue_loan import issue_loan
from library.interfaces.api.resources.loans import LoansResource

loans = LoansResource(issue_loan=issue_loan)
