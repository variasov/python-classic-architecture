INSERT INTO library.readers (full_name, email, phone, tier, valid_until, is_blocked)
VALUES (
    %(full_name)s,
    %(contact_email)s,
    %(contact_phone)s,
    %(membership_tier)s,
    %(membership_valid_until)s,
    %(is_blocked)s
)
RETURNING id
