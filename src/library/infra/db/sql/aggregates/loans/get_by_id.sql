SELECT
    l.id AS Loan__id,
    l.reader_id AS Loan__reader_id,
    l.book_id AS Loan__book_id,
    l.inventory_number AS Loan__inventory_number,
    l.issued_at AS Loan__issued_at,
    l.returned_at AS Loan__returned_at,
    l.start_date AS Period__start,
    l.due_date AS Period__due,
    e.extended_at AS Extension__extended_at,
    e.new_due AS Extension__new_due
FROM library.loans l
LEFT JOIN library.loan_extensions e ON e.loan_id = l.id
WHERE l.id = %(id)s
ORDER BY e.id
