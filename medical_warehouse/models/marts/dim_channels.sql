{{
    config(
        materialized='table'
    )
}}

-- Dimension table: Channel information
-- One row per unique Telegram channel with aggregated statistics

WITH channel_stats AS (
    SELECT
        channel_name,
        channel_title,
        MIN(message_date) AS first_post_date,
        MAX(message_date) AS last_post_date,
        COUNT(*) AS total_posts,
        AVG(view_count) AS avg_views
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name, channel_title
)

SELECT
    -- Surrogate key
    ROW_NUMBER() OVER (ORDER BY channel_name) AS channel_key,
    
    -- Channel attributes
    channel_name,
    channel_title,
    
    -- Channel classification (you can customize this logic)
    CASE 
        WHEN channel_name IN ('cheMed123', 'tikvahpharma') THEN 'Pharmaceutical'
        WHEN channel_name IN ('lobelia4cosmetics') THEN 'Cosmetics'
        WHEN channel_name IN ('tenamereja') THEN 'Medical Equipment'
        ELSE 'General Medical'
    END AS channel_type,
    
    -- Activity metrics
    first_post_date,
    last_post_date,
    total_posts,
    ROUND(avg_views::NUMERIC, 2) AS avg_views

FROM channel_stats
