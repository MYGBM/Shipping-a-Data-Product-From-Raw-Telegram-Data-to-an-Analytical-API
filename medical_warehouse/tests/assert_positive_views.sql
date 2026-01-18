-- Custom test: Ensure view counts are non-negative
-- This test fails (returns rows) if any messages have negative views

SELECT
    message_id,
    channel_name,
    view_count
FROM {{ ref('stg_telegram_messages') }}
WHERE view_count < 0
