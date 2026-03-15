WITH stg AS (
    SELECT * FROM {{ ref('stg_marketing_attribution') }}
)
SELECT
    channel,
    SUM(first_touch_credit * order_revenue) AS first_touch_revenue,
    SUM(last_touch_credit * order_revenue) AS last_touch_revenue,
    SUM(linear_credit * order_revenue) AS linear_revenue,
    SUM({{ time_decay_credit('touchpoint_date', 'order_date') }} * order_revenue) AS time_decay_revenue,
    COUNT(DISTINCT order_id) AS total_orders
FROM stg
GROUP BY 1
