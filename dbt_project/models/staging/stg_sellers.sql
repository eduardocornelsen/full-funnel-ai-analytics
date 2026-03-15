WITH source AS (
    SELECT * FROM {{ source('olist', 'sellers') }}
)
SELECT
    seller_id,
    seller_zip_code_prefix,
    LOWER(seller_city) AS seller_city,
    seller_state
FROM source
