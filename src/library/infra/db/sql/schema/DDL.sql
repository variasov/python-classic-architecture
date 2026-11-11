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

CREATE TABLE library.copies (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id integer NOT NULL REFERENCES library.books (id) ON DELETE CASCADE,
    inventory_number text NOT NULL,
    hall text NOT NULL,
    rack integer NOT NULL,
    shelf integer NOT NULL,
    is_available boolean NOT NULL DEFAULT TRUE
);

CREATE UNIQUE INDEX copies_inventory_number_uq
    ON library.copies (inventory_number);

CREATE TABLE library.readers (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name text NOT NULL,
    email text NOT NULL,
    phone text,
    tier text NOT NULL,
    valid_until date NOT NULL,
    is_blocked boolean NOT NULL DEFAULT FALSE
);

CREATE TABLE library.loans (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reader_id integer NOT NULL REFERENCES library.readers (id) ON DELETE CASCADE,
    copy_id integer NOT NULL REFERENCES library.copies (id) ON DELETE CASCADE,
    period_start date NOT NULL,
    period_due date NOT NULL,
    returned_at date
);

CREATE TABLE library.loan_extensions (
    loan_id integer NOT NULL REFERENCES library.loans (id) ON DELETE CASCADE,
    position integer NOT NULL,
    extended_at date NOT NULL,
    new_due date NOT NULL,
    PRIMARY KEY (loan_id, position)
);
