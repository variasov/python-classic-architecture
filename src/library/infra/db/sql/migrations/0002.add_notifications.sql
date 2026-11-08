-- transactional: true
-- depends: 0001.init

CREATE TABLE library.notifications (
    id bigserial PRIMARY KEY,
    message text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
