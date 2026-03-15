WITH source AS (
    SELECT * FROM {{ source('marketing', 'hubspot_contacts') }}
)
SELECT
    contact_id,
    customer_id,
    email,
    first_name,
    last_name,
    city,
    state,
    CAST(create_date AS DATE) AS create_date,
    lifecycle_stage,
    lead_source,
    num_orders,
    total_revenue,
    CAST(first_order_date AS DATE) AS first_order_date,
    CAST(last_activity_date AS DATE) AS last_activity_date
FROM source
