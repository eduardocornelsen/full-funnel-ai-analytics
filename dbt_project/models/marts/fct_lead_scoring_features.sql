WITH customer_stats AS (
    SELECT * FROM {{ ref('int_customer_ltv') }}
),
customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),
hubspot AS (
    SELECT 
        customer_id,
        MIN(lead_source) AS lead_source,
        MIN(create_date) AS lead_create_date
    FROM {{ ref('stg_hubspot_contacts') }}
    GROUP BY 1
)
SELECT
    c.customer_id,
    h.lead_source,
    cs.total_orders,
    cs.total_revenue,
    cs.avg_order_value,
    cs.customer_segment,
    c.customer_state,
    cs.is_high_value
FROM customer_stats cs
JOIN customers c ON cs.customer_id = c.customer_id
LEFT JOIN hubspot h ON c.customer_unique_id = h.customer_id
