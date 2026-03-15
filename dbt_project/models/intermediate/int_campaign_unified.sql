SELECT 
    date, 
    'google_ads' AS platform, 
    campaign_name, 
    campaign_type AS campaign_category,
    impressions, 
    clicks, 
    cost AS spend, 
    conversions, 
    conversion_value AS revenue, 
    roas
FROM {{ ref('stg_google_ads_performance') }}

UNION ALL

SELECT 
    date, 
    'meta_ads' AS platform, 
    campaign_name, 
    objective AS campaign_category,
    impressions, 
    link_clicks AS clicks, 
    spend, 
    purchases AS conversions, 
    purchase_value AS revenue, 
    roas
FROM {{ ref('stg_meta_ads_performance') }}
