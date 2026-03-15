WITH source AS (
    SELECT * FROM {{ source('marketing', 'marketing_attribution') }}
)
SELECT
    order_id,
    touchpoint_position,
    total_touchpoints,
    channel,
    platform,
    CAST(touchpoint_date AS DATE) AS touchpoint_date,
    CAST(order_date AS DATE) AS order_date,
    order_revenue,
    first_touch_credit,
    last_touch_credit,
    linear_credit
FROM source
