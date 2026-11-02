UPDATE library.loans
SET reader_id = %(reader_id)s, book_id = %(book_id)s, inventory_number = %(inventory_number)s,
    issued_at = %(issued_at)s, start = %(start)s, due = %(due)s, returned_at = %(returned_at)s
WHERE id = %(id)s
RETURNING id
