import falcon

from library.app.roles import Account


class AuthMiddleware:
    def __init__(self, users: dict[str, frozenset[str]]) -> None:
        self._users = users

    def process_request(
        self,
        req: falcon.Request,
        _resp: falcon.Response,
    ) -> None:
        login = req.get_header('X-User') or ''
        permissions = self._users.get(login, frozenset())
        req.context.account = Account(
            login=login,
            permissions=permissions,
        )
