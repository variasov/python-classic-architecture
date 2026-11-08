from datetime import date

from library.app.queries.loans.find_loans import (
    FindLoans,
    FindLoansParams,
    LoanDTO,
)


def test_find_loans_passes_params_and_clock_date(
    find_loans_gateway,
    clock_factory,
) -> None:
    dto = LoanDTO(
        id=1,
        reader_id=1,
        book_id=1,
        inventory_number='INV-1',
        issued_at=date(2026, 1, 1),
        due=date(2026, 1, 15),
        returned_at=None,
        extensions_count=0,
    )
    find_loans_gateway.result = [dto]
    usecase = FindLoans(
        gateway=find_loans_gateway,
        clock=clock_factory(date(2026, 3, 10)),
    )
    params = FindLoansParams(reader_id=1, only_overdue=True)
    assert usecase.run(params) == [dto]
    assert find_loans_gateway.calls == [(params, date(2026, 3, 10))]
