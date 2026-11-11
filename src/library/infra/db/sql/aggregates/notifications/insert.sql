INSERT INTO library.notifications (
    reader_id, loan_id, kind, created_at
)
VALUES (
    %(reader_id)s,
    %(loan_id)s,
    %(kind)s,
    %(created_at)s
)
RETURNING id
