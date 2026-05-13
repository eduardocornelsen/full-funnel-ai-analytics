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
),
-- Collapse granular attribution channels to platform-level so the JOIN resolves.
-- fct_marketing_attribution uses e.g. 'google_ads_search', 'meta_prospecting'
-- while int_campaign_unified uses 'google_ads', 'meta_ads'.
revenue_mapped AS (
    SELECT
        CASE
            WHEN channel LIKE 'google_ads%' THEN 'google_ads'
            WHEN channel LIKE 'meta_%'      THEN 'meta_ads'
            ELSE channel
        END AS channel,
        SUM(linear_revenue) AS linear_revenue,
        SUM(total_orders)   AS total_orders
    FROM revenue
    GROUP BY 1
)
SELECT
    COALESCE(s.channel, r.channel)                                   AS channel,
    COALESCE(s.total_spend, 0)                                       AS total_spend,
    COALESCE(r.linear_revenue, 0)                                    AS attributed_revenue,
    COALESCE(r.total_orders, 0)                                      AS total_orders,
    COALESCE(s.total_spend / NULLIF(r.total_orders, 0), 0)           AS cac,
    COALESCE(r.linear_revenue / NULLIF(s.total_spend, 0), 0)         AS roas
FROM spend s
FULL OUTER JOIN revenue_mapped r ON s.channel = r.channel
WHERE COALESCE(s.channel, r.channel) IS NOT NULL
