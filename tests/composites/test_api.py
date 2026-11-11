from typing import Any

import pytest
from falcon import testing

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


def _delete_book(raw_db: Any, isbn: str) -> None:
    raw_db.execute('DELETE FROM library.books WHERE isbn = %(isbn)s', isbn=isbn)


def _create_book(client: testing.TestClient, raw_db: Any, isbn: str) -> int:
    _delete_book(raw_db, isbn)
    response = client.simulate_post(
        '/library/books', headers={'X-User': 'admin'}, json={**BOOK, 'isbn': isbn}
    )
    assert response.status_code == 201
    book_id: Any = response.json['id']
    assert isinstance(book_id, int)
    return book_id


def test_create_book_is_saved(client: testing.TestClient, raw_db: Any) -> None:
    try:
        response = client.simulate_post(
            '/library/books', headers={'X-User': 'admin'}, json=BOOK
        )

        assert response.status_code == 201
        book_id: Any = response.json['id']
        assert isinstance(book_id, int)
        title = raw_db.scalar(
            'SELECT title FROM library.books WHERE id = %(id)s', id=book_id
        )
        assert title == 'Война и мир'
    finally:
        _delete_book(raw_db, BOOK['isbn'])


def test_transaction_rolls_back_on_error(
    client: testing.TestClient, raw_db: Any, monkeypatch: pytest.MonkeyPatch
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


def test_add_copy_to_created_book(
    client: testing.TestClient, raw_db: Any
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
    client: testing.TestClient, raw_db: Any
) -> None:
    isbn = '9785171183663'
    try:
        book_id = _create_book(client, raw_db, isbn)
        payload = {**COPY, 'book_id': book_id, 'inventory_number': 'INV-E2E-2'}
        first = client.simulate_post(
            '/library/copies', headers={'X-User': 'admin'}, json=payload
        )
        assert first.status_code == 201

        repeated = client.simulate_post(
            '/library/copies', headers={'X-User': 'admin'}, json=payload
        )

        assert repeated.status_code == 422
        detail = repeated.json[0]
        assert detail['type'] == 'InventoryNumberTaken'
        assert detail['ctx'] == {'inventory_number': 'INV-E2E-2'}
    finally:
        _delete_book(raw_db, isbn)


def test_unknown_route_is_404(client: testing.TestClient) -> None:
    assert client.simulate_get('/library/nothing').status_code == 404
