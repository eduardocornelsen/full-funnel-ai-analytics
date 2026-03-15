WITH source AS (
    SELECT * FROM {{ source('marketing', 'google_ads_daily_performance') }}
)
SELECT
    CAST(date AS DATE) AS date,
    campaign_id,
    campaign_name,
    campaign_type,
    impressions,
    clicks,
    cost,
    conversions,
    conversion_value,
    ctr,
    avg_cpc,
    cost_per_conversion,
    roas
FROM source
