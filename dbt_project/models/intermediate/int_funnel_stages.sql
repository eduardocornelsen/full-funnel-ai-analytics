WITH attribution AS (
    SELECT * FROM {{ ref('stg_marketing_attribution') }}
),
ga4 AS (
    SELECT * FROM {{ ref('stg_ga4_sessions') }}
),
hubspot AS (
    SELECT * FROM {{ ref('stg_hubspot_deals') }}
),
salesforce AS (
    SELECT * FROM {{ ref('stg_salesforce_opportunities') }}
),
orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    a.channel AS attribution_channel,
    a.platform AS attribution_platform,
    a.touchpoint_date,
    h.deal_id AS hubspot_deal_id,
    h.create_date AS hubspot_create_date,
    h.deal_stage AS hubspot_stage,
    s.opportunity_id AS sf_opportunity_id,
    s.created_date AS sf_created_date,
    s.stage AS sf_stage,
    o.order_status,
    o.order_purchase_timestamp
FROM orders o
LEFT JOIN attribution a ON o.order_id = a.order_id AND a.touchpoint_position = 1
LEFT JOIN hubspot h ON o.order_id = h.order_id
LEFT JOIN salesforce s ON o.order_id = s.order_id
