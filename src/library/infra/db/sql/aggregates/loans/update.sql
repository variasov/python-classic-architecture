UPDATE library.loans
SET reader_id = %(reader_id)s,
    copy_id = %(copy_id)s,
    period_start = %(period_start)s,
    period_due = %(period_due)s,
    returned_at = %(returned_at)s
WHERE id = %(id)s
RETURNING id
