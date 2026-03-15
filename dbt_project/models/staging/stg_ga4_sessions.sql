WITH source AS (
    SELECT * FROM {{ source('marketing', 'ga4_daily_sessions') }}
)
SELECT
    CAST(date AS DATE) AS date,
    channel_group,
    device_category,
    sessions,
    engaged_sessions,
    bounce_rate,
    avg_session_duration_sec,
    pages_per_session,
    new_users,
    conversions,
    revenue,
    conversion_rate,
    (engaged_sessions / NULLIF(sessions, 0)) * 100 AS engagement_rate
FROM source
