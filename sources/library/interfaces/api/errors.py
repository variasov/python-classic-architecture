from dataclasses import dataclass
from typing import Any

import falcon
import pydantic
from pydantic import TypeAdapter


@dataclass(frozen=True)
class ErrorDetail:
    """Контракт тела ответа с ошибкой."""

    type: str
    msg: str
    ctx: dict[str, Any]


_errors_serializer = TypeAdapter(list[ErrorDetail])


def serialize_pydantic_error(
    req: falcon.Request,
    resp: falcon.Response,
    error: pydantic.ValidationError,
    params: dict[str, Any],
) -> None:
    details = [
        ErrorDetail(
            type=item['type'],
            msg=f'{".".join(str(part) for part in item["loc"])}: {item["msg"]}',
            ctx={},
        )
        for item in error.errors(include_url=False, include_context=False)
    ]
    resp.status = falcon.HTTP_400
    resp.content_type = falcon.MEDIA_JSON
    resp.data = _errors_serializer.dump_json(details)


def serialize_app_error(
    req: falcon.Request,
    resp: falcon.Response,
    error: Exception,
    params: dict[str, Any],
) -> None:
    # Регистрируется на (AppError, DomainError); falcon типизирует error как Exception
    detail = ErrorDetail(type=type(error).__name__, msg=str(error), ctx=vars(error))
    resp.status = falcon.HTTP_422
    resp.content_type = falcon.MEDIA_JSON
    resp.data = _errors_serializer.dump_json([detail])
