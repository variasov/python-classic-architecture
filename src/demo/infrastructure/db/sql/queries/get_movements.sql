SELECT timestamp, latitude, longitude FROM movements WHERE cat_id = :cat_id ORDER BY timestamp;
