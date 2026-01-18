-- Custom test: Ensure no messages have future dates
-- This test fails (returns rows) if any messages are dated in the future

SELECT
    message_id,
    channel_name,
    message_date
FROM {{ ref('fct_messages') }} f
JOIN {{ ref('dim_dates') }} d ON f.date_key = d.date_key
WHERE d.full_date > CURRENT_DATE
