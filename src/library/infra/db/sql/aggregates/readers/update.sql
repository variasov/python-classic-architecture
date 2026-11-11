UPDATE library.readers
SET full_name = %(full_name)s,
    email = %(contact_email)s,
    phone = %(contact_phone)s,
    tier = %(membership_tier)s,
    valid_until = %(membership_valid_until)s,
    is_blocked = %(is_blocked)s
WHERE id = %(id)s
RETURNING id
