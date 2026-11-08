from typing import Any

from classic.db_tools import Engine

from library.app.commands.use_cases.loans.remind_overdue_loans import (
    NotificationsGateway,
)


class NotificationsGatewayImpl(NotificationsGateway):
    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def add(self, message: str) -> None:
        self._db.query_from('gateways/notifications/insert.sql').execute(
            message=message,
        )
