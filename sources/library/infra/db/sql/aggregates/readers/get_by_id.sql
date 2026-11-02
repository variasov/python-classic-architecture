SELECT
    r.id AS Reader__id,
    r.full_name AS Reader__full_name,
    r.is_blocked AS Reader__is_blocked,
    r.email AS Reader__email,
    r.phone AS Reader__phone,
    r.tier AS Reader__tier,
    r.valid_until AS Reader__valid_until
FROM library.readers r
WHERE r.id = %(id)s
