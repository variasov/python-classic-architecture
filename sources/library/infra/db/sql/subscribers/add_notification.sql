INSERT INTO library.notifications (kind, reader_id, loan_id, text)
VALUES (%(kind)s, %(reader_id)s, %(loan_id)s, %(text)s)
