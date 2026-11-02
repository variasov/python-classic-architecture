INSERT INTO library.loans (reader_id, book_id, inventory_number, issued_at, start, due, returned_at)
VALUES (%(reader_id)s, %(book_id)s, %(inventory_number)s, %(issued_at)s, %(start)s, %(due)s, %(returned_at)s)
RETURNING id
