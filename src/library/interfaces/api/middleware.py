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
        if login is not None and login in self._users:
            req.context.account = Account(
                login=login,
                permissions=tuple(self._users[login]),
            )


def current_account(req: falcon.Request) -> Account:
    """Аккаунт текущего запроса; без известного X-User прав нет."""
    account = getattr(req.context, 'account', None)
    if isinstance(account, Account):
        return account
    return ANONYMOUS
