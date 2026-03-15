WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),
ltv AS (
    SELECT * FROM {{ ref('int_customer_ltv') }}
),
hubspot AS (
    SELECT 
        customer_id,
        email,
        first_name,
        last_name,
        lead_source,
        create_date AS lead_create_date
    FROM {{ ref('stg_hubspot_contacts') }}
)
SELECT
    c.customer_id,
    c.customer_unique_id,
    h.email,
    h.first_name,
    h.last_name,
    c.customer_city,
    c.customer_state,
    h.lead_source,
    h.lead_create_date,
    l.total_orders,
    l.total_revenue,
    l.avg_order_value,
    l.customer_segment,
    l.is_high_value
FROM customers c
LEFT JOIN ltv l ON c.customer_id = l.customer_id
LEFT JOIN hubspot h ON c.customer_unique_id = h.customer_id
