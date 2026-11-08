from library.composites.app.commands.return_loan import return_loan
from library.interfaces.api.resources.returns import ReturnsResource

returns_resource = ReturnsResource(return_loan=return_loan)
