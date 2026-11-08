from typing import Any

from classic.db_tools import Engine
from classic.signals import Hub

from library.app.commands.signals import LoanIssued


class LoanIssuedSubscriber:
    def __init__(self, hub: Hub, db: Engine[Any]) -> None:
        self._db = db
        hub.add_reaction(LoanIssued, self._on_loan_issued)

    def _on_loan_issued(self, signal: LoanIssued) -> None:
        self._db.query_from(
            'subscribers/insert_notification.sql',
        ).execute(
            message=(
                f'Выдана книга: выдача id={signal.loan_id}, '
                f'читатель id={signal.reader_id}'
            ),
        )
