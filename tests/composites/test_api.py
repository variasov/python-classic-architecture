from datetime import datetime, timezone

from falcon import testing
from pytest_httpserver import HTTPServer


def test_book_and_copy_lifecycle(
    api_client: testing.TestClient,
    create_book,
    add_copy,
    auth_headers,
) -> None:
    book_id = create_book(isbn='9780132350884', title='Clean Code')
    add_copy(book_id, inventory_number='INV-1', hall='B', rack=2, shelf=3)

    card = api_client.simulate_get('/library/book', params={'id': book_id})
    assert card.status_code == 200
    assert card.json['title'] == 'Clean Code'
    assert card.json['copies'][0]['inventory_number'] == 'INV-1'
    assert card.json['copies'][0]['hall'] == 'B'
    assert card.json['copies'][0]['is_available'] is True

    found = api_client.simulate_get(
        '/library/books',
        params={'title__contains': 'Clean'},
        headers=auth_headers,
    )
    assert found.status_code == 200
    assert [book['id'] for book in found.json] == [book_id]


def test_create_book_from_catalog(
    api_client: testing.TestClient,
    catalog: HTTPServer,
    created_records,
    auth_headers,
) -> None:
    isbn = '9780201633610'
    catalog.expect_request(
        '/books',
        query_string={'isbn': isbn},
    ).respond_with_json(
        {
            'isbn': isbn,
            'title': 'Design Patterns',
            'authors': ['Erich Gamma'],
            'year': 1994,
        },
    )
    response = api_client.simulate_post(
        '/library/catalog_books',
        json={'isbn': isbn},
        headers=auth_headers,
    )
    assert response.status_code == 201
    book_id = int(response.json['id'])
    created_records.books.append(book_id)

    card = api_client.simulate_get('/library/book', params={'id': book_id})
    assert card.json['title'] == 'Design Patterns'
    assert card.json['authors'] == ['Erich Gamma']


def test_create_book_from_catalog_not_found(
    api_client: testing.TestClient,
    catalog: HTTPServer,
    auth_headers,
) -> None:
    isbn = '9780000000002'
    catalog.expect_request(
        '/books',
        query_string={'isbn': isbn},
    ).respond_with_data(status=404)
    response = api_client.simulate_post(
        '/library/catalog_books',
        json={'isbn': isbn},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json[0]['type'] == 'BookNotInCatalog'


def test_reader_lifecycle(
    api_client: testing.TestClient,
    create_reader,
    auth_headers,
) -> None:
    reader_id = create_reader(full_name='Пётр Петров')

    listed = api_client.simulate_get('/library/readers')
    assert listed.status_code == 200
    row = next(item for item in listed.json if item['id'] == reader_id)
    assert row['full_name'] == 'Пётр Петров'
    assert row['active_loans'] == 0
    assert row['valid_until'] == '2027-01-01'

    extended = api_client.simulate_put(
        '/library/memberships',
        json={'reader_id': reader_id, 'until': '2030-05-01'},
        headers=auth_headers,
    )
    assert extended.status_code == 200

    blocked = api_client.simulate_post(
        '/library/reader_blocks',
        json={'reader_id': reader_id},
        headers=auth_headers,
    )
    assert blocked.status_code == 200

    listed_after = api_client.simulate_get('/library/readers')
    row_after = next(
        item for item in listed_after.json if item['id'] == reader_id
    )
    assert row_after['valid_until'] == '2030-05-01'
    assert row_after['is_blocked'] is True


def test_loan_lifecycle_and_notifications(
    api_client: testing.TestClient,
    raw_db,
    create_book,
    create_reader,
    add_copy,
    issue_loan,
    auth_headers,
) -> None:
    book_id = create_book()
    add_copy(book_id)
    reader_id = create_reader()

    loan_id = issue_loan(reader_id, book_id)

    notifications = raw_db.scalar(
        'SELECT count(*) FROM library.notifications',
    )
    assert notifications >= 1

    card = api_client.simulate_get('/library/book', params={'id': book_id})
    assert card.json['copies'][0]['is_available'] is False

    active = api_client.simulate_get(
        '/library/loans',
        params={'reader_id': str(reader_id), 'only_active': 'true'},
    )
    assert [loan['id'] for loan in active.json] == [loan_id]

    extended = api_client.simulate_post(
        '/library/loan_extensions',
        json={'loan_id': loan_id, 'days': 7},
        headers=auth_headers,
    )
    assert extended.status_code == 200

    loans_after_extension = api_client.simulate_get(
        '/library/loans',
        params={'reader_id': str(reader_id)},
    )
    assert loans_after_extension.json[0]['extensions_count'] == 1

    returned = api_client.simulate_post(
        '/library/returns',
        json={'loan_id': loan_id},
        headers=auth_headers,
    )
    assert returned.status_code == 200

    active_after = api_client.simulate_get(
        '/library/loans',
        params={'only_active': 'true'},
    )
    assert loan_id not in {loan['id'] for loan in active_after.json}
    card_after = api_client.simulate_get(
        '/library/book',
        params={'id': book_id},
    )
    assert card_after.json['copies'][0]['is_available'] is True


def test_failed_issue_keeps_state(
    api_client: testing.TestClient,
    create_book,
    create_reader,
    add_copy,
    auth_headers,
) -> None:
    book_id = create_book()
    add_copy(book_id)
    reader_id = create_reader()
    api_client.simulate_post(
        '/library/reader_blocks',
        json={'reader_id': reader_id},
        headers=auth_headers,
    )

    response = api_client.simulate_post(
        '/library/loans',
        json={
            'reader_id': reader_id,
            'book_id': book_id,
            'inventory_number': 'INV-1',
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json[0]['type'] == 'ReaderCannotBorrow'

    card = api_client.simulate_get('/library/book', params={'id': book_id})
    assert card.json['copies'][0]['is_available'] is True
    loans = api_client.simulate_get('/library/loans')
    assert {loan['reader_id'] for loan in loans.json} == set()


def test_errors_are_mapped(
    api_client: testing.TestClient,
    auth_headers,
) -> None:
    denied = api_client.simulate_post(
        '/library/books',
        json={
            'isbn': '9780132350884',
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'published_year': 2008,
        },
    )
    assert denied.status_code == 422
    assert denied.json[0]['type'] == 'PermissionDenied'

    invalid = api_client.simulate_post(
        '/library/books',
        json={'isbn': '9780132350884'},
        headers=auth_headers,
    )
    assert invalid.status_code == 400

    missing = api_client.simulate_get(
        '/library/book',
        params={'id': '999999'},
    )
    assert missing.status_code == 422
    assert missing.json[0]['type'] == 'GetBookNotFound'


def test_create_book_invalid_domain_state_is_not_saved(
    api_client: testing.TestClient,
    create_book,
    auth_headers,
) -> None:
    before = api_client.simulate_get('/library/books').json
    response = api_client.simulate_post(
        '/library/books',
        json={
            'isbn': '9780132350884',
            'title': 'Future Book',
            'authors': ['Author'],
            'published_year': datetime.now(tz=timezone.utc).year + 1,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json[0]['type'] == 'PublishedYearInFuture'
    after = api_client.simulate_get('/library/books').json
    assert after == before
