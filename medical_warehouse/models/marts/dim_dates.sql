{{
    config(
        materialized='table'
    )
}}

-- Dimension table: Date dimension for time-based analysis
-- One row per unique date found in messages

WITH unique_dates AS (
    SELECT DISTINCT
        CAST(message_date AS DATE) AS date_value
    FROM {{ ref('stg_telegram_messages') }}
)

SELECT
    -- Surrogate key (integer format: YYYYMMDD)
    TO_CHAR(date_value, 'YYYYMMDD')::INTEGER AS date_key,
    
    -- Full date
    date_value AS full_date,
    
    -- Day attributes
    EXTRACT(DOW FROM date_value)::INTEGER AS day_of_week,  -- 0=Sunday, 6=Saturday
    TO_CHAR(date_value, 'Day') AS day_name,
    
    -- Week attributes
    EXTRACT(WEEK FROM date_value)::INTEGER AS week_of_year,
    
    -- Month attributes
    EXTRACT(MONTH FROM date_value)::INTEGER AS month,
    TO_CHAR(date_value, 'Month') AS month_name,
    
    -- Quarter and year
    EXTRACT(QUARTER FROM date_value)::INTEGER AS quarter,
    EXTRACT(YEAR FROM date_value)::INTEGER AS year,
    
    -- Weekend flag
    CASE 
        WHEN EXTRACT(DOW FROM date_value) IN (0, 6) THEN TRUE 
        ELSE FALSE 
    END AS is_weekend

FROM unique_dates
ORDER BY date_value
