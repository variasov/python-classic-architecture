CREATE SCHEMA library;

CREATE TABLE library.books (
    id SERIAL PRIMARY KEY,
    isbn TEXT NOT NULL,
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    published_year INTEGER NOT NULL
);

CREATE TABLE library.copies (
    book_id INTEGER NOT NULL REFERENCES library.books (id) ON DELETE CASCADE,
    inventory_number TEXT NOT NULL,
    hall TEXT NOT NULL,
    rack INTEGER NOT NULL,
    shelf INTEGER NOT NULL,
    is_available BOOLEAN NOT NULL,
    PRIMARY KEY (book_id, inventory_number)
);

CREATE TABLE library.readers (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    tier TEXT NOT NULL,
    valid_until DATE NOT NULL,
    is_blocked BOOLEAN NOT NULL
);

CREATE TABLE library.loans (
    id SERIAL PRIMARY KEY,
    reader_id INTEGER NOT NULL REFERENCES library.readers (id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES library.books (id) ON DELETE CASCADE,
    inventory_number TEXT NOT NULL,
    issued_at DATE NOT NULL,
    start DATE NOT NULL,
    due DATE NOT NULL,
    returned_at DATE
);

CREATE TABLE library.loan_extensions (
    loan_id INTEGER NOT NULL REFERENCES library.loans (id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    extended_at DATE NOT NULL,
    new_due DATE NOT NULL,
    PRIMARY KEY (loan_id, position)
);

CREATE TABLE library.notifications (
    id SERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    reader_id INTEGER NOT NULL REFERENCES library.readers (id) ON DELETE CASCADE,
    loan_id INTEGER NOT NULL REFERENCES library.loans (id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
