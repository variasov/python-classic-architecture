SELECT
    r.id AS Reader__id,
    r.full_name AS Reader__full_name,
    r.is_blocked AS Reader__is_blocked,
    r.email AS contact__email,
    r.phone AS contact__phone,
    r.tier AS membership__tier,
    r.valid_until AS membership__valid_until
FROM library.readers r
WHERE r.id = %(id)s
