INSERT INTO library.loan_extensions (loan_id, position, extended_at, new_due)
VALUES (%(loan_id)s, %(position)s, %(extended_at)s, %(new_due)s)
ON CONFLICT (loan_id, position) DO UPDATE
SET extended_at = EXCLUDED.extended_at, new_due = EXCLUDED.new_due
