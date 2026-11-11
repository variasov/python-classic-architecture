UPDATE library.copies
SET book_id = %(book_id)s,
    inventory_number = %(inventory_number)s,
    hall = %(shelf_hall)s,
    rack = %(shelf_rack)s,
    shelf = %(shelf_shelf)s,
    is_available = %(is_available)s
WHERE id = %(id)s
RETURNING id
