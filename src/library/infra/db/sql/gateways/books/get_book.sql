SELECT
    b.id AS GetBookDTO__id,
    b.isbn AS GetBookDTO__isbn,
    b.title AS GetBookDTO__title,
    b.authors AS GetBookDTO__authors,
    b.published_year AS GetBookDTO__published_year,
    c.inventory_number AS CopyDTO__inventory_number,
    c.hall AS CopyDTO__hall,
    c.rack AS CopyDTO__rack,
    c.shelf AS CopyDTO__shelf,
    c.is_available AS CopyDTO__is_available
FROM library.books b
LEFT JOIN library.copies c ON c.book_id = b.id
WHERE b.id = %(id)s
ORDER BY c.inventory_number
