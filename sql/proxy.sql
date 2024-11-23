SELECT created_timestamp, action, method, (CASE WHEN response_status_code IS NULL THEN -1 ELSE response_status_code END) as status, full_url, content
FROM proxy
ORDER BY timestamp_start DESC;