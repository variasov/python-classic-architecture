from typing import Any

from library.app.commands.loans.notify_on_loan_issued import NotifyOnLoanIssued
from library.app.commands.signals import LoanIssued


def test_notify_on_loan_issued_is_registered(api_app: Any) -> None:
    from library.composites.app.hub import hub

    reactions = hub._reactions[LoanIssued]

    assert any(
        isinstance(getattr(reaction, '__self__', None), NotifyOnLoanIssued)
        for reaction in reactions
    )
