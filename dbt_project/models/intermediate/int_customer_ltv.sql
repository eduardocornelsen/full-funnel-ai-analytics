WITH co AS (
    SELECT * FROM {{ ref('int_customer_orders') }}
)
SELECT
    customer_id, 
    total_orders, 
    total_revenue, 
    avg_order_value, 
    first_order_date, 
    last_order_date,
    CASE
        WHEN total_revenue >= 500 OR total_orders >= 3 THEN 'vip'
        WHEN total_orders >= 2 THEN 'returning'
        ELSE 'new'
    END AS customer_segment,
    CASE WHEN total_revenue > 200 AND total_orders > 1 THEN 1 ELSE 0 END AS is_high_value
FROM co
