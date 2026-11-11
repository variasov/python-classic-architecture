UPDATE library.notifications
SET reader_id = %(reader_id)s,
    loan_id = %(loan_id)s,
    kind = %(kind)s,
    created_at = %(created_at)s
WHERE id = %(id)s
RETURNING id
