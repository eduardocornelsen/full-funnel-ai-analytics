-- Utility date dimension for intermediate-layer models.
--
-- IMPORTANT: MetricFlow does NOT use this model as its time spine.
-- The MetricFlow spine is marts/metricflow_time_spine.sql.
-- This model exists for general-purpose date joins within the intermediate layer
-- (e.g., filling gaps in daily aggregations before they reach the mart layer).
--
-- Previously this model generated 2016-01-01 → 2019-12-31, which predated the
-- actual synthetic dataset by four years (data starts 2024-07-16). Updated to
-- use the same dbt vars as metricflow_time_spine.sql for consistency.
--
-- DuckDB range() end is EXCLUSIVE, so add 1 day beyond time_spine_end to ensure
-- the final day (2026-12-31) is included.

SELECT
    -- Cast the generated value to DATE; range() returns timestamps in DuckDB.
    CAST(range AS DATE) AS date_day    -- one row per calendar day
FROM range(
    -- Inclusive start: driven by dbt var, defaults to project start date.
    DATE '{{ var("time_spine_start", "2024-01-01") }}',

    -- DuckDB range() is exclusive on the upper bound, so we add 1 day to
    -- ensure the configured end date (e.g. 2026-12-31) is included.
    DATE '{{ var("time_spine_end", "2026-12-31") }}' + INTERVAL 1 DAY,

    -- Step: one calendar day per row.
    INTERVAL 1 DAY
)
