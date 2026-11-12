from library.composites.app.commands.loans.return_loan import return_loan
from library.interfaces.web_api.resources.returns import ReturnsResource

returns = ReturnsResource(return_loan=return_loan)
