SELECT
    b.id AS Book__id,
    b.isbn AS Book__isbn,
    b.title AS Book__title,
    b.authors AS Book__authors,
    b.published_year AS Book__published_year,
    c.inventory_number AS Copy__inventory_number,
    c.hall AS Shelf__hall,
    c.rack AS Shelf__rack,
    c.shelf AS Shelf__shelf,
    c.is_available AS Copy__is_available
FROM library.books b
LEFT JOIN library.copies c ON c.book_id = b.id
WHERE b.id = %(id)s
ORDER BY c.inventory_number
