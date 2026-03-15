WITH source AS (
    SELECT * FROM {{ source('olist', 'order_reviews') }}
)
SELECT
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    CAST(review_creation_date AS TIMESTAMP) AS review_creation_date,
    CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp,
    CASE WHEN review_score >= 4 THEN TRUE ELSE FALSE END AS is_positive,
    LENGTH(review_comment_message) AS review_length
FROM source
WHERE review_score IS NOT NULL
