INSERT INTO library.loan_extensions (
    loan_id,
    extended_at,
    new_due
)
VALUES (
    %(loan_id)s,
    %(extended_at)s,
    %(new_due)s
)
ON CONFLICT (loan_id, extended_at, new_due) DO NOTHING
