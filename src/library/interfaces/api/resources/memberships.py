from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.readers.extend_membership import (
    ExtendMembership,
    ExtendMembershipParams,
)
from library.app.roles import Account


class MembershipsResource:
    _params_validator: ClassVar[TypeAdapter[ExtendMembershipParams]] = TypeAdapter(
        ExtendMembershipParams,
    )

    def __init__(self, extend_membership: ExtendMembership) -> None:
        self._extend_membership = extend_membership

    def on_put(
        self,
        req: falcon.Request,
        _resp: falcon.Response,
    ) -> None:
        params = self._params_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        self._extend_membership.run(account, params)
