{{
    config(
        materialized='table'
    )
}}

-- Fact table: One row per message with foreign keys to dimensions
-- Contains metrics and references to dimension tables

SELECT
    -- Fact grain: one row per message
    s.message_id,
    
    -- Foreign keys to dimensions
    c.channel_key,
    TO_CHAR(s.message_date::DATE, 'YYYYMMDD')::INTEGER AS date_key,
    
    -- Message content
    s.message_text,
    s.message_length,
    
    -- Engagement metrics (facts)
    s.view_count,
    s.forward_count,
    
    -- Flags
    s.has_image

FROM {{ ref('stg_telegram_messages') }} s
LEFT JOIN {{ ref('dim_channels') }} c 
    ON s.channel_name = c.channel_name
