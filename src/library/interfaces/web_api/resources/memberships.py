import falcon

from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
)


class MembershipsResource:
    def __init__(self, extend_membership: ExtendMembership) -> None:
        self._extend_membership = extend_membership

    def on_put(self, req: falcon.Request, resp: falcon.Response) -> None:
        self._extend_membership.run(req.media, req.context.account)
