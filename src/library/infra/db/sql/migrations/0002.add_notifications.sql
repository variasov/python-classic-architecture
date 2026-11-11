-- transactional: true
-- depends: 0001.init

CREATE TABLE library.notifications (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reader_id integer NOT NULL REFERENCES library.readers (id) ON DELETE CASCADE,
    loan_id integer NOT NULL REFERENCES library.loans (id) ON DELETE CASCADE,
    kind text NOT NULL,
    created_at date NOT NULL
);

CREATE INDEX notifications_loan_kind_idx
    ON library.notifications (loan_id, kind);
