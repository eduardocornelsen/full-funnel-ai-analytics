-- Generating a date spine for DuckDB
SELECT
    CAST(range AS DATE) AS date_day
FROM range(DATE '2016-01-01', DATE '2020-01-01', INTERVAL 1 DAY)
