UPDATE library.readers
SET full_name = %(full_name)s, email = %(email)s, phone = %(phone)s, tier = %(tier)s,
    valid_until = %(valid_until)s, is_blocked = %(is_blocked)s
WHERE id = %(id)s
RETURNING id
