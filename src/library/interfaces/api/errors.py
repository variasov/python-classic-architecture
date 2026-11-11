from dataclasses import dataclass
from typing import Any

import falcon
import pydantic
from pydantic import TypeAdapter


@dataclass(frozen=True)
class ErrorDetail:
    """Контракт тела ответа с ошибкой"""

    type: str
    msg: str
    ctx: dict[str, Any]


_errors_serializer = TypeAdapter(list[ErrorDetail])


def _respond(
    resp: falcon.Response, status: str, details: list[ErrorDetail]
) -> None:
    resp.status = status
    resp.content_type = falcon.MEDIA_JSON
    resp.data = _errors_serializer.dump_json(details)


def serialize_validation_error(
    req: falcon.Request,  # noqa: ARG001
    resp: falcon.Response,
    error: pydantic.ValidationError,
    params: dict[str, Any],  # noqa: ARG001
) -> None:
    details = [
        ErrorDetail(
            type=str(item['type']),
            msg=str(item['msg']),
            ctx={'loc': list(item['loc'])},
        )
        for item in error.errors()
    ]
    _respond(resp, falcon.HTTP_400, details)


def serialize_auth_error(
    req: falcon.Request,  # noqa: ARG001
    resp: falcon.Response,
    error: Exception,
    params: dict[str, Any],  # noqa: ARG001
) -> None:
    _respond(resp, falcon.HTTP_403, [_detail(error)])


def serialize_app_error(
    req: falcon.Request,  # noqa: ARG001
    resp: falcon.Response,
    error: Exception,
    params: dict[str, Any],  # noqa: ARG001
) -> None:
    _respond(resp, falcon.HTTP_422, [_detail(error)])


def _detail(error: Exception) -> ErrorDetail:
    return ErrorDetail(
        type=type(error).__name__,
        msg=str(error),
        ctx=dict(vars(error)),
    )
