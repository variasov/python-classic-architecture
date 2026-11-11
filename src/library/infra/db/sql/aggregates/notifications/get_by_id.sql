SELECT
    n.id AS Notification__id,
    n.reader_id AS Notification__reader_id,
    n.loan_id AS Notification__loan_id,
    n.kind AS Notification__kind,
    n.created_at AS Notification__created_at
FROM library.notifications n
WHERE n.id = %(id)s
