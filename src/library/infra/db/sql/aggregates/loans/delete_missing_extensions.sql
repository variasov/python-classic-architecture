DELETE FROM library.loan_extensions
WHERE loan_id = %(loan_id)s
  AND (extended_at, new_due) NOT IN (
      SELECT *
      FROM unnest(
          %(extended_at)s::date[],
          %(new_due)s::date[]
      )
  )
