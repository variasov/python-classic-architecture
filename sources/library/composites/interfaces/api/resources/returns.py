from library.composites.app.commands.return_loan_command import return_loan_command
from library.interfaces.api.resources.loans import ReturnsResource

returns_resource = ReturnsResource(return_loan=return_loan_command)
