from library.composites.app.commands.extend_loan import extend_loan
from library.interfaces.web_api.resources.loan_extensions import (
    LoanExtensionsResource,
)

loan_extensions = LoanExtensionsResource(extend_loan=extend_loan)
