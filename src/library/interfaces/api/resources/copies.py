from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.books.add_copy import (
    AddCopy,
    AddCopyParams,
)
from library.app.roles import Account


class CopiesResource:
    _params_validator: ClassVar[TypeAdapter[AddCopyParams]] = TypeAdapter(
        AddCopyParams,
    )

    def __init__(self, add_copy: AddCopy) -> None:
        self._add_copy = add_copy

    def on_post(
        self,
        req: falcon.Request,
        _resp: falcon.Response,
    ) -> None:
        params = self._params_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        self._add_copy.run(account, params)
