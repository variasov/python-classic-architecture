from typing import Any

import pytest
from falcon import testing

BOOK: dict[str, Any] = {
    'isbn': '9785171183660',
    'title': 'Война и мир',
    'authors': ['Лев Толстой'],
    'published_year': 1869,
}


def _delete_book(raw_db: Any, isbn: str) -> None:
    raw_db.execute('DELETE FROM library.books WHERE isbn = %(isbn)s', isbn=isbn)


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


def test_unknown_route_is_404(client: testing.TestClient) -> None:
    assert client.simulate_get('/library/nothing').status_code == 404
