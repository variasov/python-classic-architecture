from library.composites.app.commands.extend_loan import extend_loan
from library.interfaces.api.resources.loans import LoanExtensionsResource

loan_extensions_resource = LoanExtensionsResource(extend_loan=extend_loan)
