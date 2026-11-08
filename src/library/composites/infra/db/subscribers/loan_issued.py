from library.composites.app.hub import hub
from library.composites.infra.db.engine import engine
from library.infra.db.subscribers.loan_issued import LoanIssuedSubscriber

loan_issued_subscriber = LoanIssuedSubscriber(hub=hub, db=engine)
