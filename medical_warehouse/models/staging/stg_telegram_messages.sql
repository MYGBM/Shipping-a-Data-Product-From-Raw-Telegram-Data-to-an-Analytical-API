{{
    config(
        materialized='view'
    )
}}

-- Staging model: Clean and standardize raw Telegram messages
-- This view transforms raw data into a consistent format for downstream models

SELECT
    -- Primary key
    message_id,
    
    -- Channel information
    channel_name,
    channel_title,
    
    -- Message metadata
    CAST(message_date AS TIMESTAMP) AS message_date,
    COALESCE(message_text, '') AS message_text,
    
    -- Calculated fields
    LENGTH(COALESCE(message_text, '')) AS message_length,
    
    -- Media information
    has_media,
    CASE 
        WHEN has_media = TRUE AND image_path IS NOT NULL THEN TRUE 
        ELSE FALSE 
    END AS has_image,
    image_path,
    
    -- Engagement metrics
    COALESCE(views, 0) AS view_count,
    COALESCE(forwards, 0) AS forward_count,
    
    -- Audit field
    loaded_at

FROM {{ source('raw', 'telegram_messages') }}

-- Data quality filters
WHERE 
    message_id IS NOT NULL
    AND message_date IS NOT NULL
    AND channel_name IS NOT NULL
