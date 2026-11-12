import falcon

from library.app.commands.loans.issue_loan import IssueLoan
from library.app.queries.loans.find_loans import FindLoans


class LoansResource:
    def __init__(self, find_loans: FindLoans, issue_loan: IssueLoan) -> None:
        self._find_loans = find_loans
        self._issue_loan = issue_loan

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._find_loans.run(req.params)  # pyright: ignore[reportArgumentType]

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._issue_loan.run(req.media, req.context.account)
        resp.status = falcon.HTTP_201
