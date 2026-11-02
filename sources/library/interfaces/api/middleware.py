import falcon
from library.app.roles import Account

ANONYMOUS_LOGIN = 'anonymous'


class AccountMiddleware:
    """Демо-аутентификация: строит Account из заголовка X-User."""

    def __init__(self, users: dict[str, list[str]]) -> None:
        self._users = users

    def process_request(self, req: falcon.Request, resp: falcon.Response) -> None:
        login = req.get_header('X-User') or ANONYMOUS_LOGIN
        permissions = frozenset(self._users.get(login, []))
        req.context.account = Account(login=login, permissions=permissions)


def get_account(req: falcon.Request) -> Account:
    account = req.context.account
    if not isinstance(account, Account):
        raise falcon.HTTPInternalServerError
    return account
