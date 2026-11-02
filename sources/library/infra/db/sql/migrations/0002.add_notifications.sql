-- transactional: true
-- depends: 0001.init

CREATE TABLE library.notifications (
    id SERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    reader_id INTEGER NOT NULL REFERENCES library.readers (id) ON DELETE CASCADE,
    loan_id INTEGER NOT NULL REFERENCES library.loans (id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
