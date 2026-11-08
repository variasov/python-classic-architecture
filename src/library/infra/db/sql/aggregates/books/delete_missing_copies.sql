DELETE FROM library.copies
WHERE book_id = %(book_id)s
  AND NOT (inventory_number = ANY(%(inventory_numbers)s))
