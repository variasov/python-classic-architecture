SELECT
    l.id AS Loan__id,
    l.reader_id AS Loan__reader_id,
    l.copy_id AS Loan__copy_id,
    l.returned_at AS Loan__returned_at,
    l.period_start AS period__start,
    l.period_due AS period__due,
    e.extended_at AS extension__extended_at,
    e.new_due AS extension__new_due
FROM library.loans l
LEFT JOIN library.loan_extensions e ON e.loan_id = l.id
WHERE l.id = %(id)s
ORDER BY l.id, e.position
