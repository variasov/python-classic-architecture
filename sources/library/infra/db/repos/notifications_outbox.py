from classic.db_tools import Engine
from library.app.commands.use_cases.loans.remind_overdue_loans import (
    NotificationsOutbox,
)


class DbNotificationsOutbox(NotificationsOutbox):
    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def put(self, kind: str, reader_id: int, loan_id: int, text: str) -> None:
        self._db.query_from('subscribers/add_notification.sql').execute(
            kind=kind,
            reader_id=reader_id,
            loan_id=loan_id,
            text=text,
        )
