{{
  config(
    materialized = 'table'
  )
}}

SELECT CAST(d AS DATE) AS date_day
FROM generate_series(
    '2024-01-01'::DATE,
    '2026-12-31'::DATE,
    INTERVAL '1 day'
) AS t(d)
