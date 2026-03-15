WITH spend AS (
    SELECT 
        platform AS channel,
        SUM(spend) AS total_spend
    FROM {{ ref('int_campaign_unified') }}
    GROUP BY 1
),
revenue AS (
    SELECT 
        channel,
        linear_revenue,
        total_orders
    FROM {{ ref('fct_marketing_attribution') }}
)
SELECT
    s.channel,
    COALESCE(s.total_spend, 0) AS total_spend,
    COALESCE(r.linear_revenue, 0) AS attributed_revenue,
    COALESCE(r.total_orders, 0) AS total_orders,
    COALESCE(s.total_spend / NULLIF(r.total_orders, 0), 0) AS cac,
    COALESCE(r.linear_revenue / NULLIF(s.total_spend, 0), 0) AS roas
FROM spend s
FULL OUTER JOIN revenue r ON s.channel = r.channel
