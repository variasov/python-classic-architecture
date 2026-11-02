DELETE FROM library.loan_extensions
WHERE loan_id = %(loan_id)s AND position >= %(count)s
