import falcon

from library.app.commands.use_cases.loans.return_loan import ReturnLoan


class ReturnsResource:
    def __init__(self, return_loan: ReturnLoan) -> None:
        self._return_loan = return_loan

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        self._return_loan.run(req.media, req.context.account)
