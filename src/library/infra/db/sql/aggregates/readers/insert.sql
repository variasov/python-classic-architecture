INSERT INTO library.readers (
    full_name,
    email,
    phone,
    tier,
    valid_until,
    is_blocked
)
VALUES (
    %(full_name)s,
    %(email)s,
    %(phone)s,
    %(tier)s,
    %(valid_until)s,
    %(is_blocked)s
)
RETURNING id
