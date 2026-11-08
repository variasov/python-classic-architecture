SELECT
    r.id AS ReaderDTO__id,
    r.full_name AS ReaderDTO__full_name,
    r.email AS ReaderDTO__email,
    r.phone AS ReaderDTO__phone,
    r.tier AS ReaderDTO__tier,
    r.valid_until AS ReaderDTO__valid_until,
    r.is_blocked AS ReaderDTO__is_blocked,
    (
        SELECT count(*)
        FROM library.loans l
        WHERE l.reader_id = r.id AND l.returned_at IS NULL
    ) AS ReaderDTO__active_loans,
    (
        SELECT count(*)
        FROM library.loans l
        WHERE l.reader_id = r.id
          AND l.returned_at IS NULL
          AND l.due_date < %(on)s
    ) AS ReaderDTO__overdue_loans
FROM library.readers r
ORDER BY r.id
