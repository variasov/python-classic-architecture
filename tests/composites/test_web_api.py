from datetime import date, timedelta
from typing import Any

import pytest
from falcon import testing
from pytest_httpserver import HTTPServer

from library.app.domain.loan import Loan

BOOK: dict[str, Any] = {
    'isbn': '9785171183660',
    'title': 'Война и мир',
    'authors': ['Лев Толстой'],
    'published_year': 1869,
}

COPY: dict[str, Any] = {
    'inventory_number': 'INV-E2E-1',
    'hall': 'Читальный зал',
    'rack': 2,
    'shelf': 3,
}

READER: dict[str, Any] = {
    'full_name': 'Иван Петров',
    'email': 'reader-e2e@example.com',
    'phone': '+7 900 000-00-00',
    'tier': 'premium',
    'valid_until': '2027-01-31',
}


def _catalog_payload(isbn: str) -> dict[str, Any]:
    return {
        'isbn': isbn,
        'title': 'Преступление и наказание',
        'authors': ['Фёдор Достоевский'],
        'year': 1866,
    }


def _delete_book(raw_db: Any, isbn: str) -> None:
    raw_db.execute('DELETE FROM library.books WHERE isbn = %(isbn)s', isbn=isbn)


def _delete_reader(raw_db: Any, email: str) -> None:
    raw_db.execute('DELETE FROM library.readers WHERE email = %(email)s', email=email)


def _create_book(client: testing.TestClient, raw_db: Any, isbn: str) -> int:
    _delete_book(raw_db, isbn)
    response = client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json={**BOOK, 'isbn': isbn},
    )
    assert response.status_code == 201
    book_id: Any = response.json['id']
    assert isinstance(book_id, int)
    return book_id


def test_create_book_is_saved(client: testing.TestClient, raw_db: Any) -> None:
    try:
        response = client.simulate_post(
            '/library/books',
            headers={'X-User': 'admin'},
            json=BOOK,
        )

        assert response.status_code == 201
        book_id: Any = response.json['id']
        assert isinstance(book_id, int)
        title = raw_db.scalar(
            'SELECT title FROM library.books WHERE id = %(id)s',
            id=book_id,
        )
        assert title == 'Война и мир'
    finally:
        _delete_book(raw_db, BOOK['isbn'])


def test_transaction_rolls_back_on_error(
    client: testing.TestClient,
    raw_db: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from library.infra.db.repos.books import DbBooksRepo

    def fail(self: DbBooksRepo, book: object) -> None:
        raise RuntimeError('сбой после вставки')

    monkeypatch.setattr(DbBooksRepo, '_sync_authors', fail)
    isbn = '9785171183661'

    response = client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json={**BOOK, 'isbn': isbn},
    )

    assert response.status_code == 500
    assert (
        raw_db.scalar(
            'SELECT count(*) FROM library.books WHERE isbn = %(isbn)s',
            isbn=isbn,
        )
        == 0
    )


def test_invalid_book_body_is_400(client: testing.TestClient) -> None:
    response = client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json={'isbn': BOOK['isbn'], 'authors': BOOK['authors']},
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    'params',
    [
        {'limit': '0'},
        {'title__contains': 'ab'},
        {'order_by': 'author'},
    ],
)
def test_invalid_books_search_is_400(
    client: testing.TestClient,
    params: dict[str, str],
) -> None:
    response = client.simulate_get('/library/books', params=params)

    assert response.status_code == 400


@pytest.mark.parametrize(
    ('method', 'url', 'kwargs'),
    [
        ('simulate_get', '/library/book', {}),
        ('simulate_get', '/library/readers', {'params': {'limit': '0'}}),
        ('simulate_get', '/library/loans', {'params': {'limit': '0'}}),
        ('simulate_post', '/library/catalog_books', {'json': {'isbn': '1'}}),
        ('simulate_post', '/library/copies', {'json': {'rack': 0}}),
        ('simulate_post', '/library/readers', {'json': {'email': 'x'}}),
        ('simulate_put', '/library/memberships', {'json': {'reader_id': 'x'}}),
        ('simulate_post', '/library/reader_blocks', {'json': {}}),
        ('simulate_delete', '/library/reader_blocks', {}),
        ('simulate_post', '/library/loans', {'json': {'reader_id': 1}}),
        ('simulate_post', '/library/loan_extensions', {'json': {'days': 0}}),
        ('simulate_post', '/library/returns', {'json': {}}),
    ],
)
def test_invalid_input_is_400(
    client: testing.TestClient,
    method: str,
    url: str,
    kwargs: dict[str, Any],
) -> None:
    response = getattr(client, method)(url, headers={'X-User': 'admin'}, **kwargs)

    assert response.status_code == 400


def test_add_copy_to_created_book(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    isbn = '9785171183662'
    try:
        book_id = _create_book(client, raw_db, isbn)

        response = client.simulate_post(
            '/library/copies',
            headers={'X-User': 'admin'},
            json={**COPY, 'book_id': book_id},
        )

        assert response.status_code == 201
        copy_id: Any = response.json['id']
        assert isinstance(copy_id, int)
        assert (
            raw_db.scalar(
                'SELECT inventory_number FROM library.copies WHERE id = %(id)s',
                id=copy_id,
            )
            == COPY['inventory_number']
        )
    finally:
        _delete_book(raw_db, isbn)


def test_duplicate_inventory_number_is_422(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    isbn = '9785171183663'
    try:
        book_id = _create_book(client, raw_db, isbn)
        payload = {**COPY, 'book_id': book_id, 'inventory_number': 'INV-E2E-2'}
        first = client.simulate_post(
            '/library/copies',
            headers={'X-User': 'admin'},
            json=payload,
        )
        assert first.status_code == 201

        repeated = client.simulate_post(
            '/library/copies',
            headers={'X-User': 'admin'},
            json=payload,
        )

        assert repeated.status_code == 422
        detail = repeated.json[0]
        assert detail['type'] == 'InventoryNumberTaken'
        assert detail['ctx'] == {'inventory_number': 'INV-E2E-2'}
    finally:
        _delete_book(raw_db, isbn)


def test_book_card_and_search_return_copies(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    isbn = '9785171183664'
    try:
        book_id = _create_book(client, raw_db, isbn)
        for inventory_number, rack in (
            ('INV-E2E-11', 1),
            ('INV-E2E-12', 2),
        ):
            response = client.simulate_post(
                '/library/copies',
                headers={'X-User': 'admin'},
                json={
                    **COPY,
                    'book_id': book_id,
                    'inventory_number': inventory_number,
                    'rack': rack,
                },
            )
            assert response.status_code == 201

        card = client.simulate_get(
            '/library/book',
            params={'id': str(book_id)},
        )

        assert card.status_code == 200
        assert card.json['id'] == book_id
        assert card.json['title'] == BOOK['title']
        assert card.json['authors'] == BOOK['authors']
        assert [copy['inventory_number'] for copy in card.json['copies']] == [
            'INV-E2E-11',
            'INV-E2E-12',
        ]
        assert card.json['copies'][0]['hall'] == COPY['hall']
        assert card.json['copies'][0]['rack'] == 1
        assert card.json['copies'][0]['shelf'] == COPY['shelf']
        assert card.json['copies'][0]['is_available'] is True

        found = client.simulate_get(
            '/library/books',
            params={'title__contains': 'Война'},
        )

        assert found.status_code == 200
        item = next(book for book in found.json if book['id'] == book_id)
        assert item['title'] == BOOK['title']
        assert item['available_copies'] == 2
    finally:
        _delete_book(raw_db, isbn)


def test_reader_and_loan_lists_reflect_issue_and_return(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    isbn = '9785171183671'
    email = 'reader-queries-e2e@example.com'
    _delete_book(raw_db, isbn)
    _delete_reader(raw_db, email)
    book_id: int | None = None
    reader_id: int | None = None
    try:
        book_id, copy_id, reader_id = _create_loan_entities(
            client,
            isbn,
            'INV-E2E-LIST-1',
            email,
        )

        def reader_item() -> dict[str, Any]:
            response = client.simulate_get(
                '/library/readers',
                params={'limit': '100'},
            )
            assert response.status_code == 200
            return next(item for item in response.json if item['id'] == reader_id)

        initial = reader_item()
        assert initial['full_name'] == READER['full_name']
        assert initial['email'] == email
        assert initial['active_loans'] == 0
        assert initial['overdue_loans'] == 0

        issued = client.simulate_post(
            '/library/loans',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'copy_id': copy_id},
        )
        assert issued.status_code == 201
        loan_id: int = issued.json['id']

        after_issue = reader_item()
        assert after_issue['active_loans'] == 1
        assert after_issue['overdue_loans'] == 0

        active = client.simulate_get(
            '/library/loans',
            params={'reader_id': str(reader_id), 'only_active': 'true'},
        )
        assert active.status_code == 200
        assert active.json == [
            {
                'id': loan_id,
                'reader_id': reader_id,
                'copy_id': copy_id,
                'start': str(date.today()),
                'due': str(date.today() + timedelta(days=Loan.TERM_DAYS)),
                'returned_at': None,
                'extensions_count': 0,
            },
        ]

        returned = client.simulate_post(
            '/library/returns',
            headers={'X-User': 'admin'},
            json={'loan_id': loan_id},
        )
        assert returned.status_code == 200

        assert reader_item()['active_loans'] == 0
        assert (
            client.simulate_get(
                '/library/loans',
                params={'reader_id': str(reader_id), 'only_active': 'true'},
            ).json
            == []
        )
        all_loans = client.simulate_get(
            '/library/loans',
            params={'reader_id': str(reader_id)},
        )
        assert all_loans.status_code == 200
        assert [item['id'] for item in all_loans.json] == [loan_id]
        assert all_loans.json[0]['returned_at'] == str(date.today())
    finally:
        if reader_id is not None:
            raw_db.execute(
                'DELETE FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
        if book_id is not None:
            raw_db.execute(
                'DELETE FROM library.books WHERE id = %(id)s',
                id=book_id,
            )


def test_unknown_route_is_404(client: testing.TestClient) -> None:
    assert client.simulate_get('/library/nothing').status_code == 404


def test_create_book_from_catalog(
    client: testing.TestClient,
    raw_db: Any,
    catalog_server: HTTPServer,
) -> None:
    isbn = '9785171183665'
    _delete_book(raw_db, isbn)
    catalog_server.clear()
    catalog_server.clear_all_handlers()
    catalog_server.expect_oneshot_request(
        '/books',
        query_string={'isbn': isbn},
    ).respond_with_json(_catalog_payload(isbn))
    try:
        response = client.simulate_post(
            '/library/catalog_books',
            headers={'X-User': 'admin'},
            json={'isbn': isbn},
        )

        assert response.status_code == 201
        book_id: Any = response.json['id']
        assert isinstance(book_id, int)
        assert (
            raw_db.scalar(
                'SELECT title FROM library.books WHERE id = %(id)s',
                id=book_id,
            )
            == 'Преступление и наказание'
        )
        assert (
            raw_db.scalar(
                'SELECT published_year FROM library.books WHERE id = %(id)s',
                id=book_id,
            )
            == 1866
        )
        assert raw_db.scalars(
            'SELECT name FROM library.book_authors '
            'WHERE book_id = %(id)s ORDER BY position',
            id=book_id,
        ) == ['Фёдор Достоевский']
    finally:
        _delete_book(raw_db, isbn)
        catalog_server.clear()
        catalog_server.clear_all_handlers()


def test_create_book_from_catalog_retries_temporary_failure(
    client: testing.TestClient,
    raw_db: Any,
    catalog_server: HTTPServer,
) -> None:
    isbn = '9785171183666'
    _delete_book(raw_db, isbn)
    catalog_server.clear()
    catalog_server.clear_all_handlers()
    catalog_server.expect_oneshot_request(
        '/books',
        query_string={'isbn': isbn},
    ).respond_with_data('temporary failure', status=500)
    catalog_server.expect_oneshot_request(
        '/books',
        query_string={'isbn': isbn},
    ).respond_with_json(_catalog_payload(isbn))
    try:
        response = client.simulate_post(
            '/library/catalog_books',
            headers={'X-User': 'admin'},
            json={'isbn': isbn},
        )

        assert response.status_code == 201
        book_id: Any = response.json['id']
        assert (
            raw_db.scalar(
                'SELECT title FROM library.books WHERE id = %(id)s',
                id=book_id,
            )
            == 'Преступление и наказание'
        )
        assert len(catalog_server.log) == 2
    finally:
        _delete_book(raw_db, isbn)
        catalog_server.clear()
        catalog_server.clear_all_handlers()


def test_create_book_from_catalog_does_not_retry_missing_book(
    client: testing.TestClient,
    catalog_server: HTTPServer,
) -> None:
    isbn = '9785171183667'
    catalog_server.clear()
    catalog_server.clear_all_handlers()
    catalog_server.expect_request(
        '/books',
        query_string={'isbn': isbn},
    ).respond_with_data(status=404)
    try:
        response = client.simulate_post(
            '/library/catalog_books',
            headers={'X-User': 'admin'},
            json={'isbn': isbn},
        )

        assert response.status_code == 422
        assert response.json[0]['type'] == 'BookNotInCatalog'
        assert len(catalog_server.log) == 1
    finally:
        catalog_server.clear()
        catalog_server.clear_all_handlers()


def test_register_reader_is_saved(client: testing.TestClient, raw_db: Any) -> None:
    _delete_reader(raw_db, READER['email'])
    try:
        response = client.simulate_post(
            '/library/readers',
            headers={'X-User': 'admin'},
            json=READER,
        )

        assert response.status_code == 201
        reader_id: Any = response.json['id']
        assert isinstance(reader_id, int)
        assert (
            raw_db.scalar(
                'SELECT full_name FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
            == READER['full_name']
        )
        assert (
            raw_db.scalar(
                'SELECT tier FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
            == READER['tier']
        )
        assert (
            str(
                raw_db.scalar(
                    'SELECT valid_until FROM library.readers WHERE id = %(id)s',
                    id=reader_id,
                ),
            )
            == READER['valid_until']
        )
    finally:
        _delete_reader(raw_db, READER['email'])


def test_membership_and_blocking_flow(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    email = 'reader-membership-e2e@example.com'
    _delete_reader(raw_db, email)
    try:
        registered = client.simulate_post(
            '/library/readers',
            headers={'X-User': 'admin'},
            json={**READER, 'email': email},
        )
        assert registered.status_code == 201
        reader_id: Any = registered.json['id']

        extended = client.simulate_put(
            '/library/memberships',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'valid_until': '2028-06-30'},
        )
        assert extended.status_code == 200
        assert (
            str(
                raw_db.scalar(
                    'SELECT valid_until FROM library.readers WHERE id = %(id)s',
                    id=reader_id,
                ),
            )
            == '2028-06-30'
        )
        assert (
            raw_db.scalar(
                'SELECT tier FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
            == READER['tier']
        )

        blocked = client.simulate_post(
            '/library/reader_blocks',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id},
        )
        assert blocked.status_code == 200
        assert (
            raw_db.scalar(
                'SELECT is_blocked FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
            is True
        )

        repeated = client.simulate_post(
            '/library/reader_blocks',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id},
        )
        assert repeated.status_code == 422
        assert repeated.json[0]['type'] == 'ReaderAlreadyBlocked'

        unblocked = client.simulate_delete(
            '/library/reader_blocks',
            headers={'X-User': 'admin'},
            params={'reader_id': str(reader_id)},
        )
        assert unblocked.status_code == 200
        assert (
            raw_db.scalar(
                'SELECT is_blocked FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
            is False
        )

        repeated_unblock = client.simulate_delete(
            '/library/reader_blocks',
            headers={'X-User': 'admin'},
            params={'reader_id': str(reader_id)},
        )
        assert repeated_unblock.status_code == 422
        assert repeated_unblock.json[0]['type'] == 'ReaderNotBlocked'
    finally:
        _delete_reader(raw_db, email)


def test_issue_loan_marks_copy_unavailable(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    isbn = '9785171183667'
    inventory_number = 'INV-E2E-LOAN-1'
    email = 'reader-loan-e2e@example.com'
    _delete_book(raw_db, isbn)
    _delete_reader(raw_db, email)
    book_id: int | None = None
    reader_id: int | None = None
    try:
        book = client.simulate_post(
            '/library/books',
            headers={'X-User': 'admin'},
            json={**BOOK, 'isbn': isbn},
        )
        assert book.status_code == 201
        book_id = book.json['id']

        copy = client.simulate_post(
            '/library/copies',
            headers={'X-User': 'admin'},
            json={
                **COPY,
                'book_id': book_id,
                'inventory_number': inventory_number,
            },
        )
        assert copy.status_code == 201
        copy_id = copy.json['id']

        reader = client.simulate_post(
            '/library/readers',
            headers={'X-User': 'admin'},
            json={**READER, 'email': email, 'valid_until': '2030-12-31'},
        )
        assert reader.status_code == 201
        reader_id = reader.json['id']

        issued = client.simulate_post(
            '/library/loans',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'copy_id': copy_id},
        )

        assert issued.status_code == 201
        loan_id = issued.json['id']
        assert (
            raw_db.scalar(
                'SELECT is_available FROM library.copies WHERE id = %(id)s',
                id=copy_id,
            )
            is False
        )
        assert (
            raw_db.scalar(
                'SELECT count(*) FROM library.loans WHERE id = %(id)s',
                id=loan_id,
            )
            == 1
        )

        repeated = client.simulate_post(
            '/library/loans',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'copy_id': copy_id},
        )

        assert repeated.status_code == 422
        assert repeated.json[0]['type'] == 'CopyNotAvailable'
    finally:
        if reader_id is not None:
            raw_db.execute(
                'DELETE FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
        if book_id is not None:
            raw_db.execute(
                'DELETE FROM library.books WHERE id = %(id)s',
                id=book_id,
            )


def _create_loan_entities(
    client: testing.TestClient,
    isbn: str,
    inventory_number: str,
    email: str,
) -> tuple[int, int, int]:
    book = client.simulate_post(
        '/library/books',
        headers={'X-User': 'admin'},
        json={**BOOK, 'isbn': isbn},
    )
    assert book.status_code == 201
    book_id: int = book.json['id']

    copy = client.simulate_post(
        '/library/copies',
        headers={'X-User': 'admin'},
        json={
            **COPY,
            'book_id': book_id,
            'inventory_number': inventory_number,
        },
    )
    assert copy.status_code == 201
    copy_id: int = copy.json['id']

    reader = client.simulate_post(
        '/library/readers',
        headers={'X-User': 'admin'},
        json={**READER, 'email': email, 'valid_until': '2030-12-31'},
    )
    assert reader.status_code == 201
    reader_id: int = reader.json['id']
    return book_id, copy_id, reader_id


def test_issue_loan_creates_notification(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    isbn = '9785171183669'
    email = 'reader-notification-e2e@example.com'
    _delete_book(raw_db, isbn)
    _delete_reader(raw_db, email)
    book_id: int | None = None
    reader_id: int | None = None
    try:
        book_id, copy_id, reader_id = _create_loan_entities(
            client,
            isbn,
            'INV-E2E-NOTIFY-1',
            email,
        )

        issued = client.simulate_post(
            '/library/loans',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'copy_id': copy_id},
        )

        assert issued.status_code == 201
        loan_id: int = issued.json['id']
        notification = raw_db.scalar(
            'SELECT kind FROM library.notifications WHERE loan_id = %(loan_id)s',
            loan_id=loan_id,
        )
        assert notification == 'loan_issued'
        assert (
            raw_db.scalar(
                'SELECT reader_id FROM library.notifications '
                'WHERE loan_id = %(loan_id)s',
                loan_id=loan_id,
            )
            == reader_id
        )
        assert str(
            raw_db.scalar(
                'SELECT created_at FROM library.notifications '
                'WHERE loan_id = %(loan_id)s',
                loan_id=loan_id,
            ),
        ) == str(date.today())
    finally:
        if reader_id is not None:
            raw_db.execute(
                'DELETE FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
        if book_id is not None:
            raw_db.execute(
                'DELETE FROM library.books WHERE id = %(id)s',
                id=book_id,
            )


def test_loan_rolls_back_when_notification_fails(
    client: testing.TestClient,
    raw_db: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from library.infra.db.repos.notifications import DbNotificationsRepo

    def fail(self: DbNotificationsRepo, notification: object) -> None:
        raise RuntimeError('сбой сохранения уведомления')

    isbn = '9785171183670'
    email = 'reader-notification-rollback@example.com'
    _delete_book(raw_db, isbn)
    _delete_reader(raw_db, email)
    book_id: int | None = None
    reader_id: int | None = None
    try:
        book_id, copy_id, reader_id = _create_loan_entities(
            client,
            isbn,
            'INV-E2E-NOTIFY-2',
            email,
        )
        monkeypatch.setattr(DbNotificationsRepo, 'save', fail)

        issued = client.simulate_post(
            '/library/loans',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'copy_id': copy_id},
        )

        assert issued.status_code == 500
        assert (
            raw_db.scalar(
                'SELECT count(*) FROM library.loans WHERE reader_id = %(id)s',
                id=reader_id,
            )
            == 0
        )
        assert (
            raw_db.scalar(
                'SELECT is_available FROM library.copies WHERE id = %(id)s',
                id=copy_id,
            )
            is True
        )
        assert (
            raw_db.scalar(
                'SELECT count(*) FROM library.notifications WHERE reader_id = %(id)s',
                id=reader_id,
            )
            == 0
        )
    finally:
        if reader_id is not None:
            raw_db.execute(
                'DELETE FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
        if book_id is not None:
            raw_db.execute(
                'DELETE FROM library.books WHERE id = %(id)s',
                id=book_id,
            )


def test_extend_and_return_loan_flow(
    client: testing.TestClient,
    raw_db: Any,
) -> None:
    isbn = '9785171183668'
    inventory_number = 'INV-E2E-LOAN-2'
    email = 'reader-return-e2e@example.com'
    _delete_book(raw_db, isbn)
    _delete_reader(raw_db, email)
    book_id: int | None = None
    reader_id: int | None = None
    try:
        book = client.simulate_post(
            '/library/books',
            headers={'X-User': 'admin'},
            json={**BOOK, 'isbn': isbn},
        )
        assert book.status_code == 201
        book_id = book.json['id']

        copy = client.simulate_post(
            '/library/copies',
            headers={'X-User': 'admin'},
            json={
                **COPY,
                'book_id': book_id,
                'inventory_number': inventory_number,
            },
        )
        assert copy.status_code == 201
        copy_id = copy.json['id']

        reader = client.simulate_post(
            '/library/readers',
            headers={'X-User': 'admin'},
            json={**READER, 'email': email, 'valid_until': '2030-12-31'},
        )
        assert reader.status_code == 201
        reader_id = reader.json['id']

        issued = client.simulate_post(
            '/library/loans',
            headers={'X-User': 'admin'},
            json={'reader_id': reader_id, 'copy_id': copy_id},
        )
        assert issued.status_code == 201
        loan_id = issued.json['id']

        extended = client.simulate_post(
            '/library/loan_extensions',
            headers={'X-User': 'admin'},
            json={'loan_id': loan_id, 'days': 7},
        )
        assert extended.status_code == 200
        assert raw_db.scalar(
            'SELECT period_due FROM library.loans WHERE id = %(id)s',
            id=loan_id,
        ) == date.today() + timedelta(days=Loan.TERM_DAYS + 7)
        assert (
            raw_db.scalar(
                'SELECT count(*) FROM library.loan_extensions WHERE loan_id = %(id)s',
                id=loan_id,
            )
            == 1
        )

        returned = client.simulate_post(
            '/library/returns',
            headers={'X-User': 'admin'},
            json={'loan_id': loan_id},
        )
        assert returned.status_code == 200
        assert (
            raw_db.scalar(
                'SELECT returned_at FROM library.loans WHERE id = %(id)s',
                id=loan_id,
            )
            == date.today()
        )
        assert (
            raw_db.scalar(
                'SELECT is_available FROM library.copies WHERE id = %(id)s',
                id=copy_id,
            )
            is True
        )

        repeated = client.simulate_post(
            '/library/returns',
            headers={'X-User': 'admin'},
            json={'loan_id': loan_id},
        )
        assert repeated.status_code == 422
        assert repeated.json[0]['type'] == 'LoanAlreadyReturned'
    finally:
        if reader_id is not None:
            raw_db.execute(
                'DELETE FROM library.readers WHERE id = %(id)s',
                id=reader_id,
            )
        if book_id is not None:
            raw_db.execute(
                'DELETE FROM library.books WHERE id = %(id)s',
                id=book_id,
            )
