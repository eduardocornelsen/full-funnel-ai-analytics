WITH funnel AS (
    SELECT * FROM {{ ref('int_funnel_stages') }}
)
SELECT
    attribution_channel,
    COUNT(DISTINCT order_id) AS total_touches,
    COUNT(DISTINCT hubspot_deal_id) AS total_leads,
    COUNT(DISTINCT sf_opportunity_id) AS total_opportunities,
    COUNT(DISTINCT CASE WHEN order_status = 'delivered' THEN order_id END) AS closed_won,
    SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) AS total_conversions
FROM funnel
WHERE attribution_channel IS NOT NULL
GROUP BY 1
