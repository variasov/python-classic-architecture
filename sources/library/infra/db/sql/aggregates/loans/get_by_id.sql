SELECT
    l.id AS LoanRow__id,
    l.reader_id AS LoanRow__reader_id,
    l.book_id AS LoanRow__book_id,
    l.inventory_number AS LoanRow__inventory_number,
    l.issued_at AS LoanRow__issued_at,
    l.returned_at AS LoanRow__returned_at,
    l.start AS LoanRow__start,
    l.due AS LoanRow__due,
    e.extended_at AS Extension__extended_at,
    e.new_due AS Extension__new_due
FROM library.loans l
LEFT JOIN library.loan_extensions e ON e.loan_id = l.id
WHERE l.id = %(id)s
ORDER BY e.position
