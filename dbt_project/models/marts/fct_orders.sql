WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }} 
    WHERE order_status = 'delivered'
),
items AS (
    SELECT 
        order_id, 
        COUNT(*) AS item_count, 
        SUM(price) AS items_total, 
        SUM(freight_value) AS freight_total 
    FROM {{ ref('stg_order_items') }} 
    GROUP BY 1
),
payments AS (
    SELECT 
        order_id, 
        SUM(payment_value) AS payment_total, 
        MAX(payment_type) AS primary_payment_type 
    FROM {{ ref('stg_order_payments') }} 
    GROUP BY 1
),
reviews AS (
    SELECT
        order_id,
        MAX(review_score) AS review_score,
        MAX(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END) AS is_positive
    FROM {{ ref('stg_order_reviews') }}
    GROUP BY 1
),
customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),
attribution AS (
    SELECT 
        order_id, 
        MIN(channel) AS first_touch_channel, 
        MAX(channel) AS last_touch_channel, 
        COUNT(*) AS touchpoint_count 
    FROM {{ ref('stg_marketing_attribution') }} 
    GROUP BY 1
)
SELECT
    o.order_id, o.customer_id, o.order_date, o.order_year, o.order_month,
    o.order_status, o.delivery_days, o.is_late_delivery,
    i.item_count, i.items_total, i.freight_total,
    COALESCE(p.payment_total, 0) AS revenue, p.primary_payment_type,
    r.review_score, r.is_positive AS positive_review,
    c.customer_city, c.customer_state,
    a.first_touch_channel, a.last_touch_channel, a.touchpoint_count
FROM orders o
LEFT JOIN items i ON o.order_id = i.order_id
LEFT JOIN payments p ON o.order_id = p.order_id
LEFT JOIN reviews r ON o.order_id = r.order_id
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN attribution a ON o.order_id = a.order_id
