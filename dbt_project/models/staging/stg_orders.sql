WITH source AS (
    SELECT * FROM {{ source('olist', 'orders') }}
)
SELECT
    order_id,
    customer_id,
    order_status,
    CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
    CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
    CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
    CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
    CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,
    CAST(order_purchase_timestamp AS DATE) AS order_date,
    EXTRACT(YEAR FROM CAST(order_purchase_timestamp AS TIMESTAMP)) AS order_year,
    EXTRACT(MONTH FROM CAST(order_purchase_timestamp AS TIMESTAMP)) AS order_month,
    {% if target.type == 'bigquery' %}
        TIMESTAMP_DIFF(CAST(order_delivered_customer_date AS TIMESTAMP), CAST(order_purchase_timestamp AS TIMESTAMP), DAY) AS delivery_days,
    {% elif target.type == 'postgres' %}
        EXTRACT(DAY FROM (CAST(order_delivered_customer_date AS TIMESTAMP) - CAST(order_purchase_timestamp AS TIMESTAMP))) AS delivery_days,
    {% else %}
        DATEDIFF('day', CAST(order_purchase_timestamp AS TIMESTAMP), CAST(order_delivered_customer_date AS TIMESTAMP)) AS delivery_days,
    {% endif %}
    CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN TRUE ELSE FALSE END AS is_late_delivery
FROM source
WHERE order_purchase_timestamp IS NOT NULL
