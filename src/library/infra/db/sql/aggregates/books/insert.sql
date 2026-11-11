INSERT INTO library.books (isbn, title, published_year)
VALUES (%(isbn)s, %(title)s, %(published_year)s)
RETURNING id
