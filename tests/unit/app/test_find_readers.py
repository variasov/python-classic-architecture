from datetime import date

from library.app.queries.readers.find_readers import (
    FindReaders,
    FindReadersParams,
    ReaderDTO,
)


def test_find_readers_passes_clock_date(
    find_readers_gateway,
    clock_factory,
) -> None:
    dto = ReaderDTO(
        id=1,
        full_name='Иван Иванов',
        email='ivan@example.com',
        phone=None,
        tier='basic',
        valid_until=date(2027, 1, 1),
        is_blocked=False,
        active_loans=1,
        overdue_loans=0,
    )
    find_readers_gateway.result = [dto]
    usecase = FindReaders(
        gateway=find_readers_gateway,
        clock=clock_factory(date(2026, 3, 10)),
    )
    assert usecase.run(FindReadersParams()) == [dto]
    assert find_readers_gateway.calls == [date(2026, 3, 10)]
