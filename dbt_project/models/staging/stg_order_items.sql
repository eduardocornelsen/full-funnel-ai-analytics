WITH source AS (
    SELECT * FROM {{ source('olist', 'order_items') }}
)
SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    price,
    freight_value,
    (price + freight_value) AS total_item_value,
    CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date
FROM source
