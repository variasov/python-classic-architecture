SELECT
    b.id AS BookCard__id,
    b.isbn AS BookCard__isbn,
    b.title AS BookCard__title,
    b.authors AS BookCard__authors,
    b.published_year AS BookCard__published_year,
    c.inventory_number AS CopyCard__inventory_number,
    c.is_available AS CopyCard__is_available,
    c.hall AS CopyCard__hall,
    c.rack AS CopyCard__rack,
    c.shelf AS CopyCard__shelf
FROM library.books b
LEFT JOIN library.copies c ON c.book_id = b.id
WHERE b.id = %(id)s
ORDER BY c.inventory_number
