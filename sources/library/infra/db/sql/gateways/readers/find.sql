SELECT
    r.id AS FoundReader__id,
    r.full_name AS FoundReader__full_name,
    r.email AS FoundReader__email,
    r.tier AS FoundReader__tier,
    r.valid_until AS FoundReader__valid_until,
    r.is_blocked AS FoundReader__is_blocked,
    count(l.id) FILTER (WHERE l.returned_at IS NULL)::int AS FoundReader__active_loans,
    count(l.id) FILTER (WHERE l.returned_at IS NULL AND l.due < %(today)s)::int
        AS FoundReader__overdue_loans
FROM library.readers r
LEFT JOIN library.loans l ON l.reader_id = r.id
GROUP BY r.id
ORDER BY r.id
LIMIT %(limit)s OFFSET %(offset)s
