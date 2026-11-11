INSERT INTO library.copies (book_id, inventory_number, hall, rack, shelf, is_available)
VALUES (
    %(book_id)s,
    %(inventory_number)s,
    %(shelf_hall)s,
    %(shelf_rack)s,
    %(shelf_shelf)s,
    %(is_available)s
)
RETURNING id
