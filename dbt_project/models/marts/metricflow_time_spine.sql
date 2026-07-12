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
-- The spine start is a dbt var; the END defaults to one year past today's
-- build date so the spine can never silently cap a growing dataset. A literal
-- end date here would recreate the 2026-07 staleness bug on a longer fuse:
-- the mart's bounds CTE can only clip to spine rows that exist, so a spine
-- frozen at a fixed date freezes the mart the day the data passes it.
-- Override for pinned snapshots:
--   dbt build --vars '{"time_spine_start":"2024-01-01","time_spine_end":"2027-12-31"}'
--
-- The column MUST be named `date_day` — MetricFlow looks for this exact name
-- when it discovers the time spine model.

SELECT
    CAST(d AS DATE) AS date_day
FROM generate_series(
    '{{ var("time_spine_start", "2024-01-01") }}'::DATE,
    {% if var("time_spine_end", none) %}'{{ var("time_spine_end") }}'::DATE{% else %}current_date + INTERVAL '1 year'{% endif %},
    INTERVAL '1 day'
) AS t(d)
