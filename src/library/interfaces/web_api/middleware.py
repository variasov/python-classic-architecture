from collections.abc import Collection, Mapping

import falcon

from library.app.roles import Account

ANONYMOUS = Account(login='anonymous', permissions=())


class UserMiddleware:
    """Демо-аутентификация: строит Account по заголовку X-User."""

    def __init__(self, users: Mapping[str, Collection[str]]) -> None:
        self._users = users

    def process_request(self, req: falcon.Request, resp: falcon.Response) -> None:
        login = req.get_header('X-User')
        req.context.account = ANONYMOUS
        if login is not None and login in self._users:
            req.context.account = Account(
                login=login,
                permissions=tuple(self._users[login]),
            )
