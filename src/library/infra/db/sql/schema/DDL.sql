CREATE SCHEMA IF NOT EXISTS library;

CREATE TABLE library.books (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    isbn text NOT NULL,
    title text NOT NULL,
    published_year integer NOT NULL
);

CREATE TABLE library.book_authors (
    book_id integer NOT NULL REFERENCES library.books (id) ON DELETE CASCADE,
    position integer NOT NULL,
    name text NOT NULL,
    PRIMARY KEY (book_id, position)
);
