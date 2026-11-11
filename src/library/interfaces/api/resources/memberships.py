from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
    ExtendMembershipParams,
)
from library.interfaces.api.middleware import current_account


class MembershipsResource:
    _extend_validator: ClassVar = TypeAdapter(ExtendMembershipParams)

    def __init__(self, extend_membership: ExtendMembership) -> None:
        self._extend_membership = extend_membership

    def on_put(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._extend_validator.validate_json(req.bounded_stream.read())
        self._extend_membership.run(params, current_account(req))
