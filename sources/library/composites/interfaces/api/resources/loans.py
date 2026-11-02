from library.composites.app.commands.issue_loan_command import issue_loan_command
from library.composites.app.queries.find_loans import find_loans
from library.interfaces.api.resources.loans import LoansResource

loans_resource = LoansResource(find_loans=find_loans, issue_loan=issue_loan_command)
