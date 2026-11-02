from classic.db_tools import Engine
from classic.signals import Hub
from library.app.commands.signals import LoanIssued


class LoanIssuedNotifier:
    """Пишет в outbox уведомление о выдаче."""

    def __init__(self, engine: Engine, hub: Hub) -> None:
        self._db = engine
        hub.add_reaction(LoanIssued, self._on_loan_issued)

    def _on_loan_issued(self, signal: LoanIssued) -> None:
        self._db.query_from('subscribers/add_notification.sql').execute(
            kind='loan_issued',
            reader_id=signal.reader_id,
            loan_id=signal.loan_id,
            text=f'Выдача {signal.loan_id} оформлена',
        )
