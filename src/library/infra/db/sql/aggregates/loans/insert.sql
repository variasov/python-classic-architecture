INSERT INTO library.loans (
    reader_id, copy_id, period_start, period_due, returned_at
)
VALUES (
    %(reader_id)s,
    %(copy_id)s,
    %(period_start)s,
    %(period_due)s,
    %(returned_at)s
)
RETURNING id
