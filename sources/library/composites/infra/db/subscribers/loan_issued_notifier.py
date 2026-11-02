from library.composites.app.hub import hub
from library.composites.infra.db.engine import engine
from library.infra.db.subscribers.loan_issued_notifier import LoanIssuedNotifier

loan_issued_notifier = LoanIssuedNotifier(engine=engine, hub=hub)
