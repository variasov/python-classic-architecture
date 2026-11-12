import falcon

from library.app.commands.use_cases.loans.extend_loan import ExtendLoan


class LoanExtensionsResource:
    def __init__(self, extend_loan: ExtendLoan) -> None:
        self._extend_loan = extend_loan

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        self._extend_loan.run(req.media, req.context.account)
