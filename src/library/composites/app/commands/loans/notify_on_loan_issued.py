from library.app.commands.loans.notify_on_loan_issued import NotifyOnLoanIssued
from library.composites.app.hub import hub
from library.composites.infra.db.repos.notifications import notifications_repo

notify_on_loan_issued = NotifyOnLoanIssued(hub=hub, notifications=notifications_repo)
