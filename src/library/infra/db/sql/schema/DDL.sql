CREATE SCHEMA IF NOT EXISTS library;

CREATE TABLE library.books (
    id bigserial PRIMARY KEY,
    isbn varchar(13) NOT NULL,
    title text NOT NULL,
    authors text[] NOT NULL DEFAULT '{}',
    published_year integer NOT NULL
);

CREATE TABLE library.copies (
    book_id bigint NOT NULL
        REFERENCES library.books (id) ON DELETE CASCADE,
    inventory_number text NOT NULL,
    hall text NOT NULL,
    rack integer NOT NULL,
    shelf integer NOT NULL,
    is_available boolean NOT NULL DEFAULT true,
    PRIMARY KEY (book_id, inventory_number)
);

CREATE TABLE library.readers (
    id bigserial PRIMARY KEY,
    full_name text NOT NULL,
    email text NOT NULL,
    phone text,
    tier text NOT NULL,
    valid_until date NOT NULL,
    is_blocked boolean NOT NULL DEFAULT false
);

CREATE TABLE library.loans (
    id bigserial PRIMARY KEY,
    reader_id bigint NOT NULL
        REFERENCES library.readers (id) ON DELETE CASCADE,
    book_id bigint NOT NULL
        REFERENCES library.books (id) ON DELETE CASCADE,
    inventory_number text NOT NULL,
    issued_at date NOT NULL,
    start_date date NOT NULL,
    due_date date NOT NULL,
    returned_at date
);

CREATE TABLE library.loan_extensions (
    id bigserial PRIMARY KEY,
    loan_id bigint NOT NULL
        REFERENCES library.loans (id) ON DELETE CASCADE,
    extended_at date NOT NULL,
    new_due date NOT NULL,
    UNIQUE (loan_id, extended_at, new_due)
);

CREATE TABLE library.notifications (
    id bigserial PRIMARY KEY,
    message text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
