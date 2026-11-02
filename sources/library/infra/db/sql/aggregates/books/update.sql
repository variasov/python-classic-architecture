UPDATE library.books
SET isbn = %(isbn)s, title = %(title)s, authors = %(authors)s, published_year = %(published_year)s
WHERE id = %(id)s
RETURNING id
