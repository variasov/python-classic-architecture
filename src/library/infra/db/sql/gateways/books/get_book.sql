SELECT
    b.id AS BookCardDTO__id,
    b.isbn AS BookCardDTO__isbn,
    b.title AS BookCardDTO__title,
    b.published_year AS BookCardDTO__published_year,
    COALESCE(ba.authors, ARRAY[]::text[]) AS BookCardDTO__authors,
    c.id AS copy__id,
    c.inventory_number AS copy__inventory_number,
    c.hall AS copy__hall,
    c.rack AS copy__rack,
    c.shelf AS copy__shelf,
    c.is_available AS copy__is_available
FROM library.books b
LEFT JOIN (
    SELECT book_id, array_agg(name ORDER BY position) AS authors
    FROM library.book_authors
    GROUP BY book_id
) ba ON ba.book_id = b.id
LEFT JOIN library.copies c ON c.book_id = b.id
WHERE b.id = %(id)s
ORDER BY c.id
