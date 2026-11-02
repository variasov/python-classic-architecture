from collections.abc import Callable
from datetime import timedelta

import pytest
from classic.db_tools import Engine
from classic.signals import Hub
from library.app.commands.domain.book import Book
from library.app.commands.domain.loan import Loan
from library.app.commands.domain.reader import Reader
from library.app.commands.signals import LoanIssued
from library.app.queries.books.find_books import FindBooksParams
from library.app.queries.loans.find_loans import FindLoansParams
from library.app.queries.readers.find_readers import FindReadersParams
from library.infra.db.gateways.book_card_gateway import DbBookCardGateway
from library.infra.db.gateways.books_search_gateway import DbBooksSearchGateway
from library.infra.db.gateways.loans_search_gateway import DbLoansSearchGateway
from library.infra.db.gateways.readers_search_gateway import DbReadersSearchGateway
from library.infra.db.repos.loans_repo import DbLoansRepo
from library.infra.db.repos.notifications_outbox import DbNotificationsOutbox
from library.infra.db.subscribers.loan_issued_notifier import LoanIssuedNotifier

from tests.conftest import TODAY, RawDb


def test_books_filters(
    books_search_gateway: DbBooksSearchGateway,
    book_factory: Callable[..., Book],
    marker: str,
) -> None:
    old = book_factory(title=f'Старая {marker}', published_year=1990, authors=['Лев'])
    new = book_factory(
        title=f'Новая {marker}',
        published_year=2020,
        authors=['Антон'],
        copies=2,
    )

    def search(**kw: object) -> set[int | None]:
        params = FindBooksParams(title__contains=marker, **kw)  # type: ignore[arg-type]
        return {b.id for b in books_search_gateway.find(params)}

    assert search() == {old.id, new.id}
    assert search(author='Лев') == {old.id}
    assert search(only_available=True) == {new.id}
    assert search(year_from=2000) == {new.id}
    assert search(year_to=2000) == {old.id}
    assert search(year_from=1990, year_to=1990) == {old.id}
    assert search(author='Антон', only_available=True, year_from=2000) == {new.id}
    assert search(author='Нет такого') == set()


def test_books_mapping(
    books_search_gateway: DbBooksSearchGateway,
    book_factory: Callable[..., Book],
    marker: str,
) -> None:
    book = book_factory(copies=2)
    book.take_copy(book.copies[0].inventory_number)
    found = books_search_gateway.find(FindBooksParams(title__contains=marker))
    assert [(b.id, b.authors, b.available_copies) for b in found] == [
        (book.id, ['Автор'], 2),
    ]


@pytest.mark.parametrize('order_by', ['title', 'published_year', 'isbn'])
def test_books_sorting_and_pagination(
    books_search_gateway: DbBooksSearchGateway,
    book_factory: Callable[..., Book],
    marker: str,
    order_by: str,
) -> None:
    first = book_factory(title=f'A {marker}', published_year=1990, isbn='9780306406157')
    second = book_factory(
        title=f'B {marker}',
        published_year=2000,
        isbn='9785171183660',
    )
    params = FindBooksParams(title__contains=marker, order_by=order_by)  # type: ignore[arg-type]
    assert [b.id for b in books_search_gateway.find(params)] == [first.id, second.id]
    page = FindBooksParams(title__contains=marker, order_by=order_by, limit=1, offset=1)  # type: ignore[arg-type]
    assert [b.id for b in books_search_gateway.find(page)] == [second.id]


def test_book_card(
    book_card_gateway: DbBookCardGateway,
    book_factory: Callable[..., Book],
) -> None:
    book = book_factory(copies=2)
    assert book.id is not None
    card = book_card_gateway.get(book.id)
    assert card is not None
    assert [c.inventory_number for c in card.copies] == sorted(
        c.inventory_number for c in book.copies
    )
    assert card.copies[0].shelf.hall == 'A'
    assert book_card_gateway.get(-1) is None


def test_book_card_without_copies(
    book_card_gateway: DbBookCardGateway,
    book_factory: Callable[..., Book],
) -> None:
    book = book_factory()
    assert book.id is not None
    card = book_card_gateway.get(book.id)
    assert card is not None
    assert card.copies == []


def test_readers_counts(
    readers_search_gateway: DbReadersSearchGateway,
    loan_factory: Callable[..., Loan],
    reader_factory: Callable[..., Reader],
    book_factory: Callable[..., Book],
    db_loans_repo: DbLoansRepo,
) -> None:
    reader = reader_factory()
    book = book_factory(copies=3)
    loan_factory(reader=reader, book=book, due_in_days=-2)
    loan_factory(reader=reader, book=book, due_in_days=5)
    returned = loan_factory(reader=reader, book=book, due_in_days=-3)
    returned.close(TODAY)
    db_loans_repo.save(returned)
    found = {
        r.id: r
        for r in readers_search_gateway.find(FindReadersParams(limit=100), TODAY)
    }
    assert reader.id is not None
    row = found[reader.id]
    assert (row.active_loans, row.overdue_loans) == (2, 1)
    assert row.email == reader.contact.email


def test_readers_pagination(
    readers_search_gateway: DbReadersSearchGateway,
    reader_factory: Callable[..., Reader],
) -> None:
    reader_factory()
    reader_factory()
    assert len(readers_search_gateway.find(FindReadersParams(limit=1), TODAY)) == 1
    assert readers_search_gateway.find(FindReadersParams(offset=10_000), TODAY) == []


def test_loans_filters(
    loans_search_gateway: DbLoansSearchGateway,
    loan_factory: Callable[..., Loan],
    reader_factory: Callable[..., Reader],
    db_loans_repo: DbLoansRepo,
) -> None:
    reader = reader_factory()
    overdue = loan_factory(reader=reader, due_in_days=-1)
    active = loan_factory(reader=reader, due_in_days=7)
    done = loan_factory(reader=reader, due_in_days=3)
    done.close(TODAY)
    db_loans_repo.save(done)
    active.extend(on=TODAY, days=2)
    db_loans_repo.save(active)

    def search(**kw: object) -> set[int | None]:
        params = FindLoansParams(reader_id=reader.id, **kw)  # type: ignore[arg-type]
        return {x.id for x in loans_search_gateway.find(params, TODAY)}

    assert search() == {overdue.id, active.id, done.id}
    assert search(only_overdue=True) == {overdue.id}
    assert search(only_active=True) == {overdue.id, active.id}
    assert search(only_active=True, only_overdue=True) == {overdue.id}
    found = loans_search_gateway.find(
        FindLoansParams(reader_id=reader.id, limit=1),
        TODAY,
    )
    assert len(found) == 1
    by_id = {
        x.id: x
        for x in loans_search_gateway.find(FindLoansParams(reader_id=reader.id), TODAY)
    }
    assert active.id is not None
    assert by_id[active.id].extensions_count == 1
    assert by_id[active.id].due == TODAY + timedelta(days=9)
    assert by_id[done.id or 0].returned_at == TODAY


def test_loan_issued_notifier_writes_outbox(
    db_engine: Engine,
    raw_db: RawDb,
    loan_factory: Callable[..., Loan],
) -> None:
    hub = Hub()
    LoanIssuedNotifier(engine=db_engine, hub=hub)
    loan = loan_factory()
    assert loan.id is not None
    hub.notify(LoanIssued(loan_id=loan.id, reader_id=loan.reader_id))
    kind = raw_db.scalar(
        'SELECT kind FROM library.notifications WHERE loan_id = %(id)s',
        id=loan.id,
    )
    assert kind == 'loan_issued'


def test_notifications_outbox(
    db_notifications_outbox: DbNotificationsOutbox,
    raw_db: RawDb,
    loan_factory: Callable[..., Loan],
) -> None:
    loan = loan_factory()
    assert loan.id is not None
    db_notifications_outbox.put('overdue_reminder', loan.reader_id, loan.id, 'текст')
    row = raw_db.scalar(
        'SELECT text FROM library.notifications WHERE loan_id = %(id)s',
        id=loan.id,
    )
    assert row == 'текст'
