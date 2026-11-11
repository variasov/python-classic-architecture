SELECT
    b.id AS Book__id,
    b.isbn AS Book__isbn,
    b.title AS Book__title,
    b.published_year AS Book__published_year,
    COALESCE(
        array_agg(a.name ORDER BY a.position) FILTER (WHERE a.name IS NOT NULL),
        '{}'
    ) AS Book__authors
FROM library.books b
LEFT JOIN library.book_authors a ON a.book_id = b.id
WHERE b.id = %(id)s
GROUP BY b.id, b.isbn, b.title, b.published_year
