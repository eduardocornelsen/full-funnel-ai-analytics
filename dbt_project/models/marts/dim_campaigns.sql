SELECT 
    campaign_id, 
    campaign_name, 
    'google_ads' AS platform, 
    campaign_type AS campaign_category
FROM {{ ref('stg_google_ads_performance') }}
GROUP BY 1, 2, 3, 4

UNION ALL

SELECT 
    campaign_id, 
    campaign_name, 
    'meta_ads' AS platform, 
    objective AS campaign_category
FROM {{ ref('stg_meta_ads_performance') }}
GROUP BY 1, 2, 3, 4
