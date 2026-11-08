INSERT INTO library.loans (
    reader_id,
    book_id,
    inventory_number,
    issued_at,
    start_date,
    due_date,
    returned_at
)
VALUES (
    %(reader_id)s,
    %(book_id)s,
    %(inventory_number)s,
    %(issued_at)s,
    %(start_date)s,
    %(due_date)s,
    %(returned_at)s
)
RETURNING id
