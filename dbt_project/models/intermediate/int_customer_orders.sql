WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }} 
    WHERE order_status = 'delivered'
),
payments AS (
    SELECT 
        order_id, 
        SUM(payment_value) AS order_revenue 
    FROM {{ ref('stg_order_payments') }} 
    GROUP BY 1
)
SELECT
    o.customer_id,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(p.order_revenue) AS total_revenue,
    AVG(p.order_revenue) AS avg_order_value,
    {% if target.type == 'bigquery' %}
        DATE_DIFF(MAX(o.order_date), MIN(o.order_date), DAY) / NULLIF(COUNT(DISTINCT o.order_id) - 1, 0) AS avg_days_between_orders
    {% elif target.type == 'postgres' %}
        EXTRACT(DAY FROM (MAX(o.order_date) - MIN(o.order_date))) / NULLIF(COUNT(DISTINCT o.order_id) - 1, 0) AS avg_days_between_orders
    {% else %}
        DATEDIFF('day', MIN(o.order_date), MAX(o.order_date)) / NULLIF(COUNT(DISTINCT o.order_id) - 1, 0) AS avg_days_between_orders
    {% endif %}
FROM orders o
LEFT JOIN payments p ON o.order_id = p.order_id
GROUP BY 1
