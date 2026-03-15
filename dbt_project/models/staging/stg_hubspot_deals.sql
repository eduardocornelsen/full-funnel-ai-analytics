WITH source AS (
    SELECT * FROM {{ source('marketing', 'hubspot_deals') }}
)
SELECT
    deal_id,
    order_id,
    deal_name,
    deal_stage,
    pipeline,
    amount,
    CAST(create_date AS DATE) AS create_date,
    CAST(NULLIF(close_date, '') AS DATE) AS close_date,
    deal_type,
    lead_source,
    CASE WHEN deal_stage = 'closed_won' THEN TRUE ELSE FALSE END AS is_closed_won
FROM source
