DELETE FROM library.copies
WHERE book_id = %(book_id)s AND inventory_number <> ALL (%(inventory_numbers)s::text[])
