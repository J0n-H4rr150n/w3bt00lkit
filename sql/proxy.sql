SELECT created_timestamp, action, response_status_code as status, response_reason as reason, full_url
FROM proxy
ORDER BY timestamp_start DESC;