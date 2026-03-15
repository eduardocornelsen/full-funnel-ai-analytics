WITH products AS (
    SELECT * FROM {{ ref('stg_products') }}
),
order_items AS (
    SELECT 
        product_id,
        COUNT(*) AS total_units_sold,
        SUM(price) AS total_revenue,
        AVG(price) AS avg_price
    FROM {{ ref('stg_order_items') }}
    GROUP BY 1
),
reviews AS (
    SELECT 
        i.product_id,
        AVG(r.review_score) AS avg_review_score
    FROM {{ ref('stg_order_reviews') }} r
    JOIN {{ ref('stg_order_items') }} i ON r.order_id = i.order_id
    GROUP BY 1
)
SELECT
    p.*,
    COALESCE(oi.total_units_sold, 0) AS total_units_sold,
    COALESCE(oi.total_revenue, 0) AS total_revenue,
    COALESCE(oi.avg_price, 0) AS avg_price,
    COALESCE(r.avg_review_score, 0) AS avg_review_score
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN reviews r ON p.product_id = r.product_id
