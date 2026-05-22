-- Must be a physical table, not a view.
-- MetricFlow reads the time spine once per query and materialising it as a table
-- avoids re-executing generate_series() on every MetricFlow request.
{{ config(materialized = 'table') }}

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
    CAST(d AS DATE) AS date_day
FROM generate_series(
    '{{ var("time_spine_start", "2024-01-01") }}'::DATE,
    '{{ var("time_spine_end", "2026-12-31") }}'::DATE,
    INTERVAL '1 day'
) AS t(d)
