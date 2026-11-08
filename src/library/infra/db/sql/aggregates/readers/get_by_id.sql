SELECT
    r.id AS Reader__id,
    r.full_name AS Reader__full_name,
    r.email AS Contact__email,
    r.phone AS Contact__phone,
    r.tier AS Membership__tier,
    r.valid_until AS Membership__valid_until,
    r.is_blocked AS Reader__is_blocked
FROM library.readers r
WHERE r.id = %(id)s
