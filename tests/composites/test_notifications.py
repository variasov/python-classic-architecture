from typing import Any

from library.app.domain.events import LoanIssued
from library.app.domain.notify_on_loan_issued import NotifyOnLoanIssued


def test_notify_on_loan_issued_is_registered(api_app: Any) -> None:
    from library.composites.app.hub import hub

    reactions = hub._reactions[LoanIssued]

    assert any(
        isinstance(getattr(reaction, '__self__', None), NotifyOnLoanIssued)
        for reaction in reactions
    )
