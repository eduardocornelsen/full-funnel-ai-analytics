WITH source AS (
    SELECT * FROM {{ source('marketing', 'salesforce_opportunities') }}
)
SELECT
    opportunity_id,
    order_id,
    opportunity_name,
    stage,
    probability,
    amount,
    CAST(created_date AS DATE) AS created_date,
    CAST(close_date AS DATE) AS close_date,
    lead_source,
    type,
    fiscal_quarter,
    CASE WHEN stage = 'Closed Won' THEN TRUE ELSE FALSE END AS is_won,
    (amount * probability / 100) AS weighted_amount
FROM source
