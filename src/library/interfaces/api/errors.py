from dataclasses import dataclass
from typing import Any

import falcon
import pydantic
from pydantic import TypeAdapter

from library.app.commands.domain.errors import DomainError
from library.app.errors import AppError


@dataclass(frozen=True)
class ErrorDetail:
    type: str
    msg: str
    ctx: dict[str, Any]


_errors_serializer: TypeAdapter[list[ErrorDetail]] = TypeAdapter(
    list[ErrorDetail],
)


def _response_with_error(
    resp: falcon.Response,
    status: str,
    detail: ErrorDetail,
) -> None:
    resp.status = status
    resp.content_type = falcon.MEDIA_JSON
    resp.data = _errors_serializer.dump_json([detail])


def serialize_validation_error(
    req: falcon.Request,  # noqa: ARG001
    resp: falcon.Response,
    error: Exception,
    params: dict[str, Any],  # noqa: ARG001
) -> None:
    _response_with_error(
        resp,
        falcon.HTTP_400,
        ErrorDetail(
            type=type(error).__name__,
            msg=str(error),
            ctx={},
        ),
    )


def serialize_app_error(
    req: falcon.Request,  # noqa: ARG001
    resp: falcon.Response,
    error: Exception,
    params: dict[str, Any],  # noqa: ARG001
) -> None:
    _response_with_error(
        resp,
        falcon.HTTP_422,
        ErrorDetail(
            type=type(error).__name__,
            msg=str(error),
            ctx=dict(vars(error)),
        ),
    )


def register_error_handlers(app: falcon.App) -> None:
    app.add_error_handler(
        pydantic.ValidationError,
        serialize_validation_error,
    )
    app.add_error_handler(
        (AppError, DomainError),
        serialize_app_error,
    )
