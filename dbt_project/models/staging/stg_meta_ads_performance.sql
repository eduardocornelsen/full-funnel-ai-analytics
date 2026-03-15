WITH source AS (
    SELECT * FROM {{ source('marketing', 'meta_ads_daily_performance') }}
)
SELECT
    CAST(date AS DATE) AS date,
    campaign_id,
    campaign_name,
    objective,
    impressions,
    reach,
    spend,
    link_clicks,
    ctr,
    cpc,
    cpm,
    purchases,
    purchase_value,
    cost_per_purchase,
    roas
FROM source
