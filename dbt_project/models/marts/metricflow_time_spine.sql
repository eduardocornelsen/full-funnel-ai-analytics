{{
  config(
    -- Must be a physical table, not a view.
    -- MetricFlow reads the time spine once per query and materialising it as a table
    -- avoids re-executing generate_series() on every MetricFlow request.
    materialized = 'table'
  )
}}

-- MetricFlow time spine — one row per calendar day.
--
-- This is the ONLY authoritative date spine MetricFlow uses for all time-grain
-- aggregations (day / week / month / quarter / year). Every semantic model that
-- declares a time dimension is implicitly joined to this spine when you run
-- `mf query --metrics <m> --group-by metric_time__month`.
--
-- Bounds are driven by dbt vars (time_spine_start / time_spine_end) defined in
-- dbt_project.yml. Override at run-time with:
--   dbt build --vars '{"time_spine_start":"2024-01-01","time_spine_end":"2027-12-31"}'
--
-- The column MUST be named `date_day` — MetricFlow looks for this exact name
-- when it discovers the time spine model.

SELECT
    -- Cast the generated timestamp to DATE; MetricFlow requires a DATE type column.
    CAST(d AS DATE) AS date_day
FROM generate_series(
    -- Inclusive lower bound: start of the MetricFlow spine.
    -- Defaults to 2024-01-01 if the var is not set.
    '{{ var("time_spine_start", "2024-01-01") }}'::DATE,

    -- Inclusive upper bound: extend this when data grows past 2026-12-31.
    -- Defaults to 2026-12-31 if the var is not set.
    '{{ var("time_spine_end", "2026-12-31") }}'::DATE,

    -- Step size: daily — MetricFlow requires day-level granularity as the base.
    -- Coarser grains (week, month, quarter) are computed from this daily spine at query time.
    INTERVAL '1 day'
) AS t(d)
