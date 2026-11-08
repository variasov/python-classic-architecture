INSERT INTO library.books (isbn, title, authors, published_year)
VALUES (%(isbn)s, %(title)s, %(authors)s, %(published_year)s)
RETURNING id
