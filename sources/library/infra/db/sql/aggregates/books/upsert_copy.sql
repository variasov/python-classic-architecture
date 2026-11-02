INSERT INTO library.copies (book_id, inventory_number, hall, rack, shelf, is_available)
VALUES (%(book_id)s, %(inventory_number)s, %(hall)s, %(rack)s, %(shelf)s, %(is_available)s)
ON CONFLICT (book_id, inventory_number) DO UPDATE
SET hall = EXCLUDED.hall, rack = EXCLUDED.rack, shelf = EXCLUDED.shelf,
    is_available = EXCLUDED.is_available
