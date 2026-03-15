SELECT
    order_date,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(revenue) AS total_revenue,
    AVG(revenue) AS avg_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(DISTINCT CASE WHEN order_date = first_order_date THEN customer_id END) AS new_customers
FROM {{ ref('fct_orders') }}
LEFT JOIN (
    SELECT customer_id, MIN(order_date) as first_order_date 
    FROM {{ ref('fct_orders') }} 
    GROUP BY 1
) USING (customer_id)
GROUP BY 1
