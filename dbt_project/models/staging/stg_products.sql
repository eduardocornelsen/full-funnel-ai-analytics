WITH products AS (
    SELECT * FROM {{ source('olist', 'products') }}
),
translations AS (
    SELECT * FROM {{ source('olist', 'category_translation') }}
)
SELECT
    p.product_id,
    COALESCE(t.product_category_name_english, p.product_category_name) AS product_category_name,
    p.product_name_lenght,
    p.product_description_lenght,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    (p.product_length_cm * p.product_height_cm * p.product_width_cm) AS product_volume
FROM products p
LEFT JOIN translations t ON p.product_category_name = t.product_category_name
WHERE p.product_category_name IS NOT NULL
